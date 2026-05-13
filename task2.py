import hashlib
import time
import sys


CORRUPTED_FILE = "data_gen/test_128mb_corrupted.bin"
TRUSTED_TREE_FILE = "data_gen/trusted_merkle_tree.bin"

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

def load_trusted_tree(filename: str) -> list[list[bytes]]:
    raw = read_binary_file(filename)
    level_sizes = []
    n = NUM_BLOCKS
    while n >= 1:
        level_sizes.append(n)
        if n == 1:
            break
        n //= 2

    tree: list[list[bytes]] = []
    offset = 0
    for size in level_sizes:
        level = []
        for _ in range(size):
            h = raw[offset:offset + HASH_SIZE]
            level.append(h)
            offset += HASH_SIZE
        tree.append(level)

    return tree

def build_merkle_tree(blocks: list[bytes]) -> list[list[bytes]]:
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

    return tree


def locate_error(
    trusted_tree: list[list[bytes]],
    corrupted_tree: list[list[bytes]],
) -> tuple[int, int]:
    height = len(trusted_tree) - 1   
    comparison_count = 0
    node_idx = 0

    for level in range(height, 0, -1):
        left_child_idx = node_idx * 2
        right_child_idx = node_idx * 2 + 1
        child_level = level - 1  

        trusted_left = trusted_tree[child_level][left_child_idx]
        corrupted_left = corrupted_tree[child_level][left_child_idx]

        comparison_count += 1

        if trusted_left != corrupted_left:
            node_idx = left_child_idx
        else:
            node_idx = right_child_idx

    return node_idx, comparison_count

def main():
    print("=" * 60)
    print("Task 2 – Efficient Error Localization")
    print("=" * 60)

    print(f"\nLoading trusted Merkle Tree from '{TRUSTED_TREE_FILE}' …")
    trusted_tree = load_trusted_tree(TRUSTED_TREE_FILE)
    trusted_root = trusted_tree[-1][0]
    print(f"  Trusted root : {trusted_root.hex()}")
    print(f"  Tree height  : {len(trusted_tree) - 1}")

    print(f"\nBuilding Merkle Tree from corrupted file '{CORRUPTED_FILE}' …")
    data = read_binary_file(CORRUPTED_FILE)
    blocks = split_into_blocks(data)
    corrupted_tree = build_merkle_tree(blocks)
    corrupted_root = corrupted_tree[-1][0]
    print(f"  Corrupted root : {corrupted_root.hex()}")

    if trusted_root == corrupted_root:
        print("\n  Roots are IDENTICAL – no corruption detected.")
        return

    print("\nRunning locate_error() …")
    corrupted_block, comparison_count = locate_error(trusted_tree, corrupted_tree)

    height = len(trusted_tree) - 1
    print(f"\n[Results]")
    print(f"  Trusted root       : {trusted_root.hex()}")
    print(f"  Corrupted root     : {corrupted_root.hex()}")
    print(f"  Corrupted block    : {corrupted_block}")
    print(f"  Comparison count   : {comparison_count}")
    print(f"  Tree height H      : {height}  (log2({NUM_BLOCKS}) = {NUM_BLOCKS.bit_length() - 1})")
    assert comparison_count == height, "BUG: comparison count should equal tree height!"
    print(f"  ✓  Comparisons == H == log2(N)  →  O(log n) verified")


if __name__ == "__main__":
    main()
