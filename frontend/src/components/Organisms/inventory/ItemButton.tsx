import styles from "./ItemButton.module.css";
import Image from "next/image";
import { ItemScreenData } from "@/src/features/types/item_types";

type ItemData = {
    id: number;
    item: ItemScreenData;
    quantity: number;
}

type Props = {
    inventoryItem: ItemData;
    onSelectItemDetail: (item: ItemScreenData, quantity: number) => void;
    handleUseItem: (inventoryItemId: number) => void;
}

export default function ItemButton(props: Props) {
    const { inventoryItem, onSelectItemDetail, handleUseItem } = props;

    return (
        <div
            key={inventoryItem.id}
            className={styles.itemCard}
            onClick={() => onSelectItemDetail(inventoryItem.item, inventoryItem.quantity)}
        >
            <Image src="/game/img/アイコン/回復_アイコン.png" alt={inventoryItem.item.name} width={100} height={100} className={styles.itemIcon} />
            <p className={styles.itemName}>{inventoryItem.item.name}</p>
            <p className={styles.itemQuantity}>({inventoryItem.quantity})</p>
            <button
                type="button"
                className={styles.useButton}
                onClick={(e) => {
                    e.stopPropagation();
                    handleUseItem(inventoryItem.id);
                }}
            >
                使用
            </button>
        </div>
    );
}