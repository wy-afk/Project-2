import hashlib
import time
import sys


INPUT_FILE = "data_gen/test_128mb.bin"
NUM_BLOCKS = 128
BLOCK_SIZE = 1024 * 1024  
TOTAL_SIZE = NUM_BLOCKS * BLOCK_SIZE
HASH_SIZE = 32         

def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def read_binary_file(filename: str) -> bytes:
    with open(filename, "rb") as f:
        return f.read()


def split_into_blocks(data: bytes) -> list[bytes]:
    if len(data) != TOTAL_SIZE:
        raise ValueError(
            f"File size mismatch: expected {TOTAL_SIZE} bytes, got {len(data)} bytes"
        )
    return [data[i * BLOCK_SIZE:(i + 1) * BLOCK_SIZE] for i in range(NUM_BLOCKS)]

def compute_single_hash(data: bytes) -> tuple[bytes, float]:
    start = time.perf_counter()
    digest = sha256(data)
    elapsed = time.perf_counter() - start
    return digest, elapsed


def build_merkle_tree(blocks: list[bytes]) -> tuple[list[list[bytes]], float]:
    start = time.perf_counter()

    tree: list[list[bytes]] = []
    current_level = [sha256(block) for block in blocks]
    tree.append(current_level)

    while len(current_level) > 1:
        next_level = []
        for i in range(0, len(current_level), 2):
            parent = sha256(current_level[i] + current_level[i + 1])
            next_level.append(parent)
        tree.append(next_level)
        current_level = next_level

    elapsed = time.perf_counter() - start
    return tree, elapsed


def internal_node_memory(tree: list[list[bytes]]) -> int:
    return sum(len(level) * HASH_SIZE for level in tree[1:])

def main():
    print("=" * 60)
    print("Task 1 – Single Hash vs. Merkle Tree")
    print("=" * 60)

    print(f"\nReading '{INPUT_FILE}' …")
    data = read_binary_file(INPUT_FILE)
    blocks = split_into_blocks(data)
    print(f"File loaded: {len(data) / (1024 * 1024):.0f} MB, {NUM_BLOCKS} blocks × {BLOCK_SIZE // 1024} KB")

    print("\n[1] Single Hash")
    single_hash, single_time = compute_single_hash(data)
    print(f"  SHA-256 : {single_hash.hex()}")
    print(f"  Time    : {single_time * 1000:.2f} ms")

    print("\n[2] Merkle Tree")
    tree, merkle_time = build_merkle_tree(blocks)
    root = tree[-1][0]
    mem = internal_node_memory(tree)

    total_hashes = sum(len(level) for level in tree)
    height = len(tree) - 1  

    print(f"  Root          : {root.hex()}")
    print(f"  Time          : {merkle_time * 1000:.2f} ms")
    print(f"  Tree height   : {height}  (log2({NUM_BLOCKS}) = {NUM_BLOCKS.bit_length() - 1})")
    print(f"  Total hashes  : {total_hashes}")
    print(f"  Internal nodes: {total_hashes - NUM_BLOCKS}  ({mem} bytes / {mem / 1024:.1f} KB)")

    print("\n[Summary]")
    print(f"  Single hash time : {single_time * 1000:.2f} ms")
    print(f"  Merkle tree time : {merkle_time * 1000:.2f} ms")
    ratio = merkle_time / single_time if single_time > 0 else float("inf")
    print(f"  Overhead ratio   : {ratio:.2f}×  (Merkle vs. single hash)")
    print("\nDone.")


if __name__ == "__main__":
    main()
