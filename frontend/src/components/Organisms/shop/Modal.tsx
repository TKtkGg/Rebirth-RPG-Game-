import styles from "./Modal.module.css";
import { ShopDisplayItem } from "@/src/features/shop/types";
import { ShopScreenData } from "@/src/features/shop/types";
import { useState } from "react";
import { PrimaryButton } from "../../atoms/button/PrimaryButton";

type Props = {
    closeModal: () => void;
    confirmPurchase: (purchaseQuantity: number) => void;
    selectedItem: ShopDisplayItem;
    data: ShopScreenData | null;
}

export function Modal(props: Props) {
    const { closeModal, confirmPurchase, selectedItem, data } = props;

    const [purchaseQuantity, setPurchaseQuantity] = useState(1);

    return (
        <div className={styles.modalOverlay} onClick={closeModal}>
            <div className={styles.modalContent} onClick={(event) => event.stopPropagation()}>
                <div className={styles.modalText}>
                    {selectedItem.name} を
                    {selectedItem.type === "item" ? `${purchaseQuantity}個` : ""}
                    購入しますか？
                </div>
                <div className={styles.modalGold}>所持金 : {data?.player.gold ?? 0}G</div>
                {selectedItem.type === "item" && (
                    <div className={styles.quantitySelector}>
                        <button
                            type="button"
                            className={styles.quantityButton}
                            onClick={() => setPurchaseQuantity((prev) => Math.max(1, prev - 1))}
                            disabled={purchaseQuantity <= 1}
                        >
                            &lt;
                        </button>
                        <div className={styles.quantityDisplay}>{purchaseQuantity}</div>
                        <button
                            type="button"
                            className={styles.quantityButton}
                            onClick={() =>
                                setPurchaseQuantity((prev) =>
                                    Math.min(selectedItem.current_stock, prev + 1)
                                )
                            }
                            disabled={purchaseQuantity >= selectedItem.current_stock}
                        >
                            &gt;
                        </button>
                    </div>
                )}
                <div className={styles.modalButtons}>
                    <PrimaryButton
                        onClick={() => confirmPurchase(purchaseQuantity)}
                        disabled={purchaseQuantity <= 0}
                    >
                        Yes
                    </PrimaryButton>
                    <PrimaryButton
                        onClick={closeModal}
                    >
                        No
                    </PrimaryButton>
                </div>
            </div>
        </div>
    );
}