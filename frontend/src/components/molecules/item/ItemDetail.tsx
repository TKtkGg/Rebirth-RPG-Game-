import styles from "./ItemDetail.module.css";
import { ItemScreenData } from "@/src/features/types/item_types";

type Props = {
    itemDetail: {
        item: ItemScreenData;
        quantity: number;
    } | null;
}

export default function ItemDetail(props: Props) {
    const { itemDetail } = props;
    return (
        <div>
            {itemDetail ? (
                <>
                    <h2 className={styles.detailTitle}>{itemDetail.item.name}</h2>
                    <p className={styles.detailDescription}>{itemDetail.item.description}</p>
                    <p className={styles.detailStats}>{itemDetail.item.target.toUpperCase()} : +{itemDetail.item.effect_amount}</p>
                    <p className={styles.detailCount}>所持数 : {itemDetail.quantity}</p>
                </>
            ) : (
                <>
                    <h2 className={styles.detailTitle}>-</h2>
                    <p className={styles.detailDescription}>アイテムを選択してください</p>
                    <p className={styles.detailStats}>-</p>
                    <p className={styles.detailCount}>所持数 : 0</p>
                </>
            )}
        </div>
    );
}