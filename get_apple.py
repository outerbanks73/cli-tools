#!/usr/bin/env python3
"""
get_apple.py — Fetch Apple Podcasts transcripts by episode ID.

Requires macOS 15.5+ with Apple Podcasts installed and Xcode CLI tools.
Uses Apple's private AMSMescal framework (FairPlay) to authenticate.

Usage:
    python3 get_apple.py <episode_id> <output_file>
    python3 get_apple.py <episode_id> <output_file> --ttml   # save raw TTML XML

Example:
    python3 get_apple.py 1000753754819 transcript.txt
"""

import sys
import os
import json
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError

CACHE_PATH = os.path.expanduser("~/.apple_podcast_bearer_token")
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

        // AMSURLRequest *urlRequest = [[AMSURLRequestClass alloc] initWithRequest:nsRequest]
        id urlRequest = ((msg_id_id)objc_msgSend)(
            [AMSURLRequestClass alloc],
            sel_registerName("initWithRequest:"),
            nsRequest
        );
        // [urlRequest setValue:timestamp forHTTPHeaderField:@"x-request-timestamp"]
        ((msg_void_id_str)objc_msgSend)(urlRequest, sel_registerName("setValue:forHTTPHeaderField:"), timestamp, @"x-request-timestamp");
        ((msg_void_id_str)objc_msgSend)(urlRequest, sel_registerName("setValue:forHTTPHeaderField:"), storeFront, @"X-Apple-Store-Front");

        // id signature = [AMSMescal _signedActionDataFromRequest:urlRequest policy:...]
        NSDictionary *policy = @{
            @"fields": @[@"clientId"],
            @"headers": @[@"x-apple-store-front", @"x-apple-client-application", @"x-request-timestamp"]
        };
        id signature = ((msg_id_id_id)objc_msgSend)(
            (id)AMSMescal,
            sel_registerName("_signedActionDataFromRequest:policy:"),
            urlRequest, policy
        );

        // id session = [AMSMescalSession defaultSession]
        id session = ((msg_id)objc_msgSend)((id)AMSMescalSession, sel_registerName("defaultSession"));
        // id urlBag = [[IMURLBag alloc] init]
        id urlBag = ((msg_id)objc_msgSend)([IMURLBag alloc], sel_registerName("init"));

        dispatch_semaphore_t sema = dispatch_semaphore_create(0);

        // id signedPromise = [session signData:signature bag:urlBag]
        id signedPromise = ((msg_id_id_id)objc_msgSend)(session, sel_registerName("signData:bag:"), signature, urlBag);

        // [signedPromise thenWithBlock:^(id result) { ... }]
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


def get_bearer_token():
    """Get bearer token, using 30-day cache if available."""
    if os.path.exists(CACHE_PATH):
        age = datetime.now().timestamp() - os.path.getmtime(CACHE_PATH)
        if age < CACHE_VALIDITY:
            with open(CACHE_PATH) as f:
                token = f.read().strip()
            if token.startswith("ey"):
                return token

    token = _compile_and_fetch_token()
    if token:
        with open(CACHE_PATH, 'w') as f:
            f.write(token)
    return token


def _compile_and_fetch_token():
    """Compile Obj-C helper, run it, return bearer token."""
    with tempfile.NamedTemporaryFile(suffix='.m', mode='w', delete=False) as src:
        src.write(OBJC_TOKEN_SOURCE)
        src_path = src.name

    bin_path = src_path.replace('.m', '')

    try:
        # Compile the Obj-C token helper
        comp = subprocess.run(
            ['clang', '-o', bin_path, src_path,
             '-Wno-objc-method-access',
             '-framework', 'Foundation',
             '-F/System/Library/PrivateFrameworks',
             '-framework', 'AppleMediaServices',
             '-fobjc-arc'],
            capture_output=True, text=True
        )
        if comp.returncode != 0:
            print(f"Compilation failed: {comp.stderr}", file=sys.stderr)
            return None

        # Run it (isolated subprocess — can segfault during cleanup, that's expected)
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


def fetch_ttml(episode_id, bearer_token):
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

    # Download TTML from CDN (no auth needed — URL has embedded access key)
    with urlopen(ttml_url) as resp:
        return resp.read().decode("utf-8")


def ttml_to_text(ttml_content):
    """Extract plain text from Apple Podcasts TTML XML."""
    root = ET.fromstring(ttml_content)

    # Collect all text from <p> elements (paragraphs/sentences)
    texts = []
    for elem in root.iter():
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag

        if tag == 'p':
            words = []
            for child in elem.iter():
                if child.text and child.text.strip():
                    words.append(child.text.strip())
            if words:
                texts.append(' '.join(words))

    return ' '.join(texts)


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 get_apple.py <episode_id> <output_file> [--ttml]")
        print("\nGet episode IDs from Apple Podcasts URLs: ?i=EPISODE_ID")
        sys.exit(1)

    episode_id = sys.argv[1]
    output_file = sys.argv[2]
    save_raw_ttml = '--ttml' in sys.argv

    if not episode_id.isdigit():
        print("Error: episode_id must be a number", file=sys.stderr)
        sys.exit(1)

    print("Getting bearer token...")
    token = get_bearer_token()
    if not token:
        print("Failed to get bearer token. Requires macOS 15.5+.", file=sys.stderr)
        sys.exit(1)
    print("Bearer token obtained.")

    print(f"Fetching transcript for episode {episode_id}...")
    ttml = fetch_ttml(episode_id, token)

    if save_raw_ttml:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(ttml)
        print(f"TTML saved to {output_file}")
    else:
        text = ttml_to_text(ttml)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Transcript saved to {output_file} ({len(text)} chars)")


if __name__ == "__main__":
    main()
