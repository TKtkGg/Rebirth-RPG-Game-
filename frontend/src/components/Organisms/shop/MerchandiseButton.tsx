import styles from "./MerchandiseButton.module.css";
import Image from "next/image";
import { ShopDisplayItem } from "@/src/features/shop/types";

type Props = {
    item: ShopDisplayItem;
    onSelectItem: (item: ShopDisplayItem) => void;
    onTooltipEnter: (item: ShopDisplayItem, x: number, y: number) => void;
    onTooltipMove: (x: number, y: number) => void;
    onTooltipLeave: () => void;
}

export const MerchandiseButton = (props: Props) => {
    const { item, onSelectItem, onTooltipEnter, onTooltipMove, onTooltipLeave } = props;

    const handleItemClick = (item: ShopDisplayItem) => {
        onSelectItem(item);
    };

    return (
        <button
            type="button"
            className={styles.shopItem}
            onClick={() => handleItemClick(item)}
            onMouseEnter={(event) => {
                onTooltipEnter(item, event.clientX + 20, event.clientY + 20);
            }}
            onMouseMove={(event) => {
                onTooltipMove(event.clientX + 20, event.clientY + 20);
            }}
            onMouseLeave={() => onTooltipLeave()}
        >
            <Image
                src={item.iconPath}
                alt={item.type}
                className={styles.shopItemIcon}
                width={92}
                height={92}
            />
            <div className={styles.shopItemName}>{item.name}</div>
            <div className={styles.shopItemPrice}>{item.price}G</div>
            {item.type === "item" && (
                <div className={styles.shopItemStock}>
                    {item.current_stock}/{item.max_stock}
                </div>
            )}
        </button>
    )
}