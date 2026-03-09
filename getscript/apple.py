"""Apple Podcasts transcript fetching."""

import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.error import HTTPError
from urllib.request import Request, urlopen

CACHE_VALIDITY = 60 * 60 * 24 * 30  # 30 days

# Obj-C source for bearer token via AMSMescal (FairPlay signing).
# Compiled and run as a subprocess to isolate potential segfaults
# from the thenWithBlock: cleanup in Apple's promise implementation.
OBJC_TOKEN_SOURCE = r'''
#import <Foundation/Foundation.h>
#import <objc/runtime.h>
#import <objc/message.h>
#import <dlfcn.h>

// Cast objc_msgSend to typed function pointers to avoid selector validation
typedef id (*msg_id)(id, SEL, ...);
typedef id (*msg_id_id)(id, SEL, id, ...);
typedef id (*msg_id_id_id)(id, SEL, id, id, ...);
typedef void (*msg_void_id_str)(id, SEL, id, NSString *);

int main() {
    @autoreleasepool {
        dlopen("/System/Library/PrivateFrameworks/PodcastsFoundation.framework/PodcastsFoundation", RTLD_LAZY);

        Class AMSMescal = objc_getClass("AMSMescal");
        Class AMSMescalSession = objc_getClass("AMSMescalSession");
        Class AMSURLRequestClass = objc_getClass("AMSURLRequest");
        Class IMURLBag = objc_getClass("IMURLBag");

        if (!AMSMescal || !AMSMescalSession || !AMSURLRequestClass || !IMURLBag) {
            fprintf(stderr, "Failed to load required Apple private frameworks. macOS 15.5+ required.\n");
            return 1;
        }

        NSString *storeFront = @"143441-1,42 t:podcasts1";
        NSDateFormatter *formatter = [[NSDateFormatter alloc] init];
        [formatter setDateFormat:@"yyyy-MM-dd'T'HH:mm:ss'Z'"];
        [formatter setTimeZone:[NSTimeZone timeZoneWithAbbreviation:@"UTC"]];
        NSString *timestamp = [formatter stringFromDate:[NSDate date]];

        NSURL *tokenURL = [NSURL URLWithString:@"https://sf-api-token-service.itunes.apple.com/apiToken?clientClass=apple&clientId=com.apple.podcasts.macos&os=OS%20X&osVersion=15.5&productVersion=1.1.0&version=2"];
        NSMutableURLRequest *nsRequest = [NSMutableURLRequest requestWithURL:tokenURL];

        id urlRequest = ((msg_id_id)objc_msgSend)(
            [AMSURLRequestClass alloc],
            sel_registerName("initWithRequest:"),
            nsRequest
        );
        ((msg_void_id_str)objc_msgSend)(urlRequest, sel_registerName("setValue:forHTTPHeaderField:"), timestamp, @"x-request-timestamp");
        ((msg_void_id_str)objc_msgSend)(urlRequest, sel_registerName("setValue:forHTTPHeaderField:"), storeFront, @"X-Apple-Store-Front");

        NSDictionary *policy = @{
            @"fields": @[@"clientId"],
            @"headers": @[@"x-apple-store-front", @"x-apple-client-application", @"x-request-timestamp"]
        };
        id signature = ((msg_id_id_id)objc_msgSend)(
            (id)AMSMescal,
            sel_registerName("_signedActionDataFromRequest:policy:"),
            urlRequest, policy
        );

        id session = ((msg_id)objc_msgSend)((id)AMSMescalSession, sel_registerName("defaultSession"));
        id urlBag = ((msg_id)objc_msgSend)([IMURLBag alloc], sel_registerName("init"));

        dispatch_semaphore_t sema = dispatch_semaphore_create(0);

        id signedPromise = ((msg_id_id_id)objc_msgSend)(session, sel_registerName("signData:bag:"), signature, urlBag);

        ((msg_id_id)objc_msgSend)(signedPromise, sel_registerName("thenWithBlock:"), ^(id result) {
            NSString *sig = [(NSData *)result base64EncodedStringWithOptions:0];

            NSMutableURLRequest *signedRequest = [NSMutableURLRequest requestWithURL:tokenURL];
            [signedRequest setValue:timestamp forHTTPHeaderField:@"x-request-timestamp"];
            [signedRequest setValue:storeFront forHTTPHeaderField:@"X-Apple-Store-Front"];
            [signedRequest setValue:sig forHTTPHeaderField:@"X-Apple-ActionSignature"];

            NSURLSessionDataTask *task = [[NSURLSession sharedSession] dataTaskWithRequest:signedRequest completionHandler:^(NSData *data, NSURLResponse *response, NSError *error) {
                NSDictionary *json = [NSJSONSerialization JSONObjectWithData:data options:0 error:nil];
                printf("%s", [json[@"token"] UTF8String]);
                dispatch_semaphore_signal(sema);
            }];
            [task resume];
            dispatch_semaphore_wait(sema, DISPATCH_TIME_FOREVER);
        });

        dispatch_semaphore_wait(sema, DISPATCH_TIME_FOREVER);
    }
    return 0;
}
'''


def _get_cache_path(cache_dir: str) -> str:
    return os.path.join(cache_dir, "apple_token")


def get_bearer_token(cache_dir: str) -> str:
    """Get bearer token, using cached version if valid."""
    cache_path = _get_cache_path(cache_dir)

    if os.path.exists(cache_path):
        age = datetime.now().timestamp() - os.path.getmtime(cache_path)
        if age < CACHE_VALIDITY:
            with open(cache_path) as f:
                token = f.read().strip()
            if token.startswith("ey"):
                return token

    token = _compile_and_fetch_token()
    if token:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w") as f:
            f.write(token)
    return token


def _compile_and_fetch_token() -> str | None:
    """Compile Obj-C helper, run it, return bearer token."""
    if sys.platform != "darwin":
        print(
            "Apple Podcasts transcripts require macOS with Xcode CLI tools.",
            file=sys.stderr,
        )
        return None

    with tempfile.NamedTemporaryFile(suffix=".m", mode="w", delete=False) as src:
        src.write(OBJC_TOKEN_SOURCE)
        src_path = src.name

    bin_path = src_path.replace(".m", "")

    try:
        comp = subprocess.run(
            [
                "clang",
                "-o",
                bin_path,
                src_path,
                "-Wno-objc-method-access",
                "-framework",
                "Foundation",
                "-F/System/Library/PrivateFrameworks",
                "-framework",
                "AppleMediaServices",
                "-fobjc-arc",
            ],
            capture_output=True,
            text=True,
        )
        if comp.returncode != 0:
            print(f"Compilation failed: {comp.stderr}", file=sys.stderr)
            return None

        result = subprocess.run([bin_path], capture_output=True, text=True, timeout=30)

        token = result.stdout.strip()
        if not token.startswith("ey"):
            print(f"Invalid token. stderr: {result.stderr}", file=sys.stderr)
            return None

        return token
    except subprocess.TimeoutExpired:
        print("Token fetch timed out", file=sys.stderr)
        return None
    finally:
        for p in (src_path, bin_path):
            if os.path.exists(p):
                os.unlink(p)


def fetch_ttml(episode_id: str, bearer_token: str) -> str:
    """Fetch TTML transcript from Apple's AMP API."""
    url = (
        f"https://amp-api.podcasts.apple.com/v1/catalog/us/podcast-episodes/"
        f"{episode_id}/transcripts?fields=ttmlToken,ttmlAssetUrls"
        f"&include%5Bpodcast-episodes%5D=podcast&l=en-US&with=entitlements"
    )

    req = Request(url)
    req.add_header("Authorization", f"Bearer {bearer_token}")

    try:
        with urlopen(req) as resp:
            data = json.loads(resp.read())
    except HTTPError as e:
        body = e.read().decode() if e.fp else ""
        raise Exception(f"AMP API returned {e.code}: {body}")

    if "errors" in data:
        raise Exception(f"API error: {data['errors']}")

    attrs = data["data"][0]["attributes"]
    ttml_url = attrs["ttmlAssetUrls"]["ttml"]

    with urlopen(ttml_url) as resp:
        return resp.read().decode("utf-8")


def ttml_to_segments(ttml_content: str) -> list[dict]:
    """Parse TTML XML into segment dicts with timestamps."""
    root = ET.fromstring(ttml_content)
    segments = []

    for elem in root.iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag

        if tag == "p":
            words = []
            for child in elem.iter():
                if child.text and child.text.strip():
                    words.append(child.text.strip())
            if words:
                text = " ".join(words)
                begin = elem.get("begin", "")
                end = elem.get("end", "")
                segment = {"text": text}
                if begin:
                    segment["start"] = _parse_ttml_time(begin)
                if end:
                    segment["end"] = _parse_ttml_time(end)
                    if "start" in segment:
                        segment["duration"] = segment["end"] - segment["start"]
                segments.append(segment)

    return segments


def ttml_to_text(ttml_content: str) -> str:
    """Extract plain text from Apple Podcasts TTML XML."""
    segments = ttml_to_segments(ttml_content)
    return " ".join(s["text"] for s in segments)


def _parse_ttml_time(time_str: str) -> float:
    """Parse TTML time format (HH:MM:SS.mmm) to seconds."""
    parts = time_str.split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    if len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    return float(time_str)
