from utils.checkpoint import (
    load_checkpoint,
    save_checkpoint,
)


checkpoint = load_checkpoint()

print("\nBEFORE:")
print(checkpoint)


checkpoint["completed"].append(
    1
)

checkpoint["results"]["1"] = (
    "Test summary for note 1."
)


save_checkpoint(
    checkpoint
)


print("\nAFTER SAVE:")
print(
    load_checkpoint()
)