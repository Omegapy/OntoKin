"""Trusted, offline local completion adapter. No model downloads and no API keys."""
import argparse
from contextlib import closing
import hashlib
import json
import sys

import llama_cpp


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gguf", help="immutable locally installed single-file coding model")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--context", type=int, default=16384)
    args = parser.parse_args()
    req = json.load(sys.stdin)
    with open(args.gguf, "rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    snapshot = "gguf-sha256:" + digest
    if snapshot != req["snapshot"] or type(req["maxOutput"]) is not int or req["maxOutput"] < 1:
        raise ValueError("wrong GGUF snapshot or invalid output allowance")
    with closing(llama_cpp.Llama(model_path=args.gguf, n_ctx=args.context, n_threads=args.threads, n_threads_batch=args.threads,
                         n_gpu_layers=0, seed=42, verbose=False)) as llm:
        # Qwen2.5 Instruct ChatML. Control markers inside an untrusted transcript remain literal text.
        before = llm.tokenize(b"<|im_start|>user\n", add_bos=False, special=True)
        content = llm.tokenize(req["prompt"].encode(), add_bos=False, special=False)
        after = llm.tokenize(b"<|im_end|>\n<|im_start|>assistant\n", add_bos=False, special=True)
        tokens = before + content + after
        stops = {llm.token_eos()}
        for marker in (b"<|im_end|>", b"<|endoftext|>"):
            ids = llm.tokenize(marker, add_bos=False, special=True)
            if len(ids) == 1:
                stops.add(ids[0])
        if len(tokens) + 1 > min(req["remainingTokens"], llm.n_ctx()):
            print(json.dumps(dict(requestId=req["requestId"], snapshot=snapshot,
                                  status="no_capacity", requiredInput=len(tokens), context=llm.n_ctx())))
            return
        llm.eval(tokens)
        max_new = min(req["maxOutput"], req["remainingTokens"] - len(tokens), llm.n_ctx() - len(tokens))
        selected = []
        for _ in range(max_new):
            token = int(llm.sample(temp=0.0))
            selected.append(token)
            if token in stops or len(selected) == max_new:
                break
            llm.eval([token])
        text = llm.detokenize(selected).decode("utf-8", errors="replace")
    print(json.dumps(dict(requestId=req["requestId"], snapshot=snapshot, text=text,
                          source="llama-cpp-python local eval and greedy sample",
                          usage={"fullInput": len(tokens), "cachedInput": 0, "output": len(selected)},
                          native={"runtime": llama_cpp.__version__, "seed": 42, "nCtx": args.context, "template": "Qwen2.5 Instruct ChatML",
                                  "nThreads": args.threads, "gpuLayers": 0, "temperature": 0,
                                  "inputIds": tokens, "generatedIds": selected,
                                  "cachePolicy": "new process, one fresh model context"})))


if __name__ == "__main__":
    main()
