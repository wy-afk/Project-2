import hashlib
import time

MAIN_FILE = "data_gen/test_128mb.bin"
NEW_BLOCK_FILE = "data_gen/test_1mb.bin"

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

def replace_node(
    tree: list[list[bytes]],
    block_index: int,
    new_block: bytes,
) -> tuple[list[list[bytes]], float]:
    start = time.perf_counter()
    updated_tree = [list(level) for level in tree]   
    updated_tree[0][block_index] = sha256(new_block)

    idx = block_index
    for level in range(1, len(updated_tree)):
        parent_idx = idx // 2
        left_idx = parent_idx * 2
        right_idx = parent_idx * 2 + 1
        updated_tree[level][parent_idx] = sha256(
            updated_tree[level - 1][left_idx] + updated_tree[level - 1][right_idx]
        )
        idx = parent_idx

    elapsed = time.perf_counter() - start
    return updated_tree, elapsed

def full_rebuild(blocks: list[bytes], block_index: int, new_block: bytes) -> tuple[list[list[bytes]], float]:
    start = time.perf_counter()
    blocks_copy = list(blocks)
    blocks_copy[block_index] = new_block
    tree = build_merkle_tree(blocks_copy)
    elapsed = time.perf_counter() - start
    return tree, elapsed

def main():
    print("=" * 60)
    print("Task 3")
    print("=" * 60)

    print(f"\nReading '{MAIN_FILE}' …")
    data = read_binary_file(MAIN_FILE)
    blocks = split_into_blocks(data)

    print(f"Reading replacement block '{NEW_BLOCK_FILE}' …")
    new_block = read_binary_file(NEW_BLOCK_FILE)
    if len(new_block) != BLOCK_SIZE:
        raise ValueError(f"Replacement block size mismatch: expected {BLOCK_SIZE}, got {len(new_block)}")

    while True:
        try:
            block_index = int(input(f"\nEnter block index to replace (0 ~ {NUM_BLOCKS - 1}): "))
            if 0 <= block_index < NUM_BLOCKS:
                break
            print("Out of range.")
        except ValueError:
            print("Invalid input.")

    print("\nBuilding original Merkle Tree …")
    orig_tree = build_merkle_tree(blocks)
    orig_root = orig_tree[-1][0]
    print(f"  Original root : {orig_root.hex()}")

    updated_tree_path, path_time = replace_node(orig_tree, block_index, new_block)
    root_path = updated_tree_path[-1][0]

    updated_tree_full, full_time = full_rebuild(blocks, block_index, new_block)
    root_full = updated_tree_full[-1][0]

    identical = root_path == root_full

    print(f"\n[Results]")
    print(f"  Block replaced         : {block_index}")
    print(f"  Original root          : {orig_root.hex()}")
    print(f"  Updated root (path)    : {root_path.hex()}")
    print(f"  Updated root (rebuild) : {root_full.hex()}")
    print(f"  Roots identical        : {'✓  YES' if identical else '✗  NO (BUG!)'}")
    print(f"\n  replace_node() time    : {path_time * 1000:.4f} ms")
    print(f"  Full rebuild time      : {full_time * 1000:.4f} ms")
    speedup = full_time / path_time if path_time > 0 else float("inf")
    print(f"  Speedup factor         : {speedup:.1f}×  (path update is faster)")

    height = len(orig_tree) - 1
    print(f"\n  Path recomputes {height + 1} hashes  (log2({NUM_BLOCKS}) + 1 = {height + 1})")
    print(f"  Full rebuild recomputes {sum(len(l) for l in orig_tree)} hashes  (all nodes)")
    print(f"\nDone.")


if __name__ == "__main__":
    main()
