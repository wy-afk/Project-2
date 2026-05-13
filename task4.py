import hashlib
CORRUPTED_FILE = "data_gen/test_128mb_corrupted.bin"
TRUSTED_TREE_FILE = "data_gen/trusted_merkle_tree.bin"
PARITY_FILE = "data_gen/parity_blocks.bin"

NUM_BLOCKS = 128
BLOCK_SIZE = 1024 * 1024 
TOTAL_SIZE = NUM_BLOCKS * BLOCK_SIZE
HASH_SIZE = 32

NUM_PARITY_BLOCKS = NUM_BLOCKS // 2

def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def read_binary_file(filename: str) -> bytes:
    with open(filename, "rb") as f:
        return f.read()


def split_into_blocks(data: bytes, block_size: int = BLOCK_SIZE) -> list[bytes]:
    total = len(data)
    num = total // block_size
    return [data[i * block_size:(i + 1) * block_size] for i in range(num)]


def xor_blocks(a: bytes, b: bytes) -> bytes:
    return bytes(x ^ y for x, y in zip(a, b))

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
        level = [raw[offset + j * HASH_SIZE: offset + (j + 1) * HASH_SIZE] for j in range(size)]
        offset += size * HASH_SIZE
        tree.append(level)
    return tree

def build_merkle_tree(blocks: list[bytes]) -> list[list[bytes]]:
    tree: list[list[bytes]] = []
    current_level = [sha256(block) for block in blocks]
    tree.append(current_level)
    while len(current_level) > 1:
        next_level = [
            sha256(current_level[i] + current_level[i + 1])
            for i in range(0, len(current_level), 2)
        ]
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
        child_level = level - 1
        trusted_left = trusted_tree[child_level][left_child_idx]
        corrupted_left = corrupted_tree[child_level][left_child_idx]
        comparison_count += 1
        if trusted_left != corrupted_left:
            node_idx = left_child_idx
        else:
            node_idx = left_child_idx + 1

    return node_idx, comparison_count

def replace_node(
    tree: list[list[bytes]],
    block_index: int,
    new_block: bytes,
) -> list[list[bytes]]:
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
    return updated_tree

def recover_block(
    corrupted_index: int,
    corrupted_blocks: list[bytes],
    parity_blocks: list[bytes],
) -> tuple[bytes, int, int]:

    if corrupted_index % 2 == 0:
        parity_idx = corrupted_index // 2
        sibling_idx = corrupted_index + 1
    else:
        parity_idx = (corrupted_index - 1) // 2
        sibling_idx = corrupted_index - 1

    parity = parity_blocks[parity_idx]
    sibling = corrupted_blocks[sibling_idx]
    recovered = xor_blocks(parity, sibling)

    return recovered, parity_idx, sibling_idx

def main():
    print("=" * 60)
    print("Task 4 – Advanced Self-Healing")
    print("=" * 60)

    print(f"\nLoading trusted Merkle Tree …")
    trusted_tree = load_trusted_tree(TRUSTED_TREE_FILE)
    trusted_root = trusted_tree[-1][0]
    print(f"  Trusted root : {trusted_root.hex()}")

    print(f"\nLoading corrupted file …")
    corrupted_data = read_binary_file(CORRUPTED_FILE)
    corrupted_blocks = split_into_blocks(corrupted_data)

    corrupted_tree = build_merkle_tree(corrupted_blocks)
    corrupted_root = corrupted_tree[-1][0]
    print(f"  Corrupted root : {corrupted_root.hex()}")

    print(f"\nLoading parity blocks …")
    parity_data = read_binary_file(PARITY_FILE)
    parity_blocks = split_into_blocks(parity_data)
    print(f"  Parity blocks loaded: {len(parity_blocks)}")

    print(f"\n[Step 1] Locating corrupted block …")
    corrupted_index, comparison_count = locate_error(trusted_tree, corrupted_tree)
    print(f"  Corrupted block index : {corrupted_index}")
    print(f"  Comparison count      : {comparison_count}  (H = log2({NUM_BLOCKS}) = {NUM_BLOCKS.bit_length()-1})")

    print(f"\n[Step 2] Recovering block using XOR parity …")
    recovered_block, parity_idx, sibling_idx = recover_block(
        corrupted_index, corrupted_blocks, parity_blocks
    )
    print(f"  Parity block index used : {parity_idx}")
    print(f"  Sibling block index     : {sibling_idx}")

    print(f"\n[Step 3] Restoring Merkle Tree …")
    repaired_tree = replace_node(corrupted_tree, corrupted_index, recovered_block)
    repaired_root = repaired_tree[-1][0]
    print(f"  Repaired root : {repaired_root.hex()}")

    verified = repaired_root == trusted_root
    print(f"\n[Results]")
    print(f"  Trusted root          : {trusted_root.hex()}")
    print(f"  Corrupted root        : {corrupted_root.hex()}")
    print(f"  Corrupted block index : {corrupted_index}")
    print(f"  Comparison count      : {comparison_count}")
    print(f"  Parity block index    : {parity_idx}")
    print(f"  Sibling block index   : {sibling_idx}")
    print(f"  Repaired root         : {repaired_root.hex()}")
    print(f"  Verification          : {'✓  PASS – repaired root matches trusted root' if verified else '✗  FAIL'}")
    print(f"\nDone.")


if __name__ == "__main__":
    main()
