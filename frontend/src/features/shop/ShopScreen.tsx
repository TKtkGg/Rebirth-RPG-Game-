"use client"

import { useEffect, useMemo, useState } from "react";
import { apiGet, apiPost } from "../../lib/apiClient";
import { ShopScreenData } from "./types";
import { EquipmentScreenData } from "../types/equipment_types";
import { ItemScreenData } from "../types/item_types";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { SectionTitle } from "@/src/components/atoms/title/SectionTitle";
import { ReturnButton } from "@/src/components/atoms/button/ReturnButton";
import styles from "./ShopScreen.module.css";

type Props = {
    playerId: string;
};

type ShopDisplayItem =
    | ({ type: "weapon" | "armor"; iconPath: string } & EquipmentScreenData)
    | ({ type: "item"; iconPath: string } & ItemScreenData);

type TooltipState = {
    item: ShopDisplayItem;
    x: number;
    y: number;
};

export default function ShopScreen(props: Props) {
    const { playerId } = props;
    const router = useRouter();
    const [data, setData] = useState<ShopScreenData | null>(null);
    const [tooltip, setTooltip] = useState<TooltipState | null>(null);
    const [selectedItem, setSelectedItem] = useState<ShopDisplayItem | null>(null);
    const [purchaseQuantity, setPurchaseQuantity] = useState(1);

    useEffect(() => {
        apiGet(`/api/shop/${playerId}/`).then((data: ShopScreenData) => {
            setData(data);
        });
    }, [playerId]);

    const handleBuyEquipment = (item: EquipmentScreenData) => {
        apiPost(`/api/shop/${playerId}/`, {
            item_name: item.name,
            item_id: item.id.toString(),
            item_price: item.price.toString(),
            item_type: item.equipment_type,
            item_quantity: "1",
        }).then((updatedData: ShopScreenData) => {
            setData(updatedData);
        });
    };

    const handleBuyItem = (item: ItemScreenData, quantity: number) => {
        apiPost(`/api/shop/${playerId}/`, {
            item_name: item.name,
            item_id: item.id.toString(),
            item_price: item.price.toString(),
            item_type: "item",
            item_quantity: quantity.toString(),
        }).then((updatedData: ShopScreenData) => {
            setData(updatedData);
        });
    };

    const displayItems = useMemo<ShopDisplayItem[]>(() => {
        if (!data) {
            return [];
        }

        const weaponItems = data.weapons.map((weapon) => ({
            ...weapon,
            type: "weapon" as const,
            iconPath: "/game/img/アイコン/武器_アイコン.png",
        }));
        const armorItems = data.armors.map((armor) => ({
            ...armor,
            type: "armor" as const,
            iconPath: "/game/img/アイコン/防具_アイコン.png",
        }));
        const itemItems = data.items.map((item) => ({
            ...item,
            type: "item" as const,
            iconPath: "/game/img/アイコン/回復_アイコン.png",
        }));

        return [...weaponItems, ...armorItems, ...itemItems].slice(0, 8);
    }, [data]);

    const handleItemClick = (item: ShopDisplayItem) => {
        setTooltip(null);
        setSelectedItem(item);
        setPurchaseQuantity(1);
    };

    const closeModal = () => {
        setSelectedItem(null);
        setPurchaseQuantity(1);
    };

    const confirmPurchase = () => {
        if (!selectedItem) {
            return;
        }

        if (selectedItem.type === "item") {
            handleBuyItem(selectedItem, purchaseQuantity);
        } else {
            handleBuyEquipment(selectedItem);
        }
        closeModal();
    };

    const renderTooltipStats = (item: ShopDisplayItem) => {
        if (item.type === "item") {
            const targetName = item.target === "hp" ? "HP" : "SP";
            return (
                <div className={styles.statLine}>
                    <span className={styles.statPositive}>
                        {targetName} : +{item.effect_amount}
                    </span>
                </div>
            );
        }

        const statLines = [
            { label: "HP", value: item.hp_bonus },
            { label: "ATK", value: item.atk_bonus },
            { label: "DEF", value: item.def_bonus },
            { label: "SPD", value: item.spd_bonus },
        ].filter((stat) => stat.value !== 0);

        return statLines.map((stat) => (
            <div className={styles.statLine} key={`${item.id}-${stat.label}`}>
                <span className={stat.value > 0 ? styles.statPositive : styles.statNegative}>
                    {stat.label} : {stat.value > 0 ? "+" : ""}
                    {stat.value}
                </span>
            </div>
        ));
    };

    return (
        <div className={`${styles.shopContainer} ${selectedItem ? styles.dimmed : ""}`}>
            <SectionTitle title="ショップ" className={styles.title} />
            <div className={styles.shopGrid}>
                {displayItems.map((item) => (
                    <button
                        key={`${item.type}-${item.id}`}
                        type="button"
                        className={styles.shopItem}
                        onClick={() => handleItemClick(item)}
                        onMouseEnter={(event) => {
                            setTooltip({
                                item,
                                x: event.clientX + 20,
                                y: event.clientY + 20,
                            });
                        }}
                        onMouseMove={(event) => {
                            setTooltip((prev) =>
                                prev
                                    ? {
                                          ...prev,
                                          x: event.clientX + 20,
                                          y: event.clientY + 20,
                                      }
                                    : null
                            );
                        }}
                        onMouseLeave={() => setTooltip(null)}
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
                ))}
            </div>

            <ReturnButton
                className={styles.backButton}
                onClick={() => router.push(`/game/battle/home/${playerId}`)}
            />

            {tooltip && (
                <div
                    className={styles.itemTooltip}
                    style={{ left: `${tooltip.x}px`, top: `${tooltip.y}px` }}
                >
                    <div className={styles.tooltipName}>{tooltip.item.name}</div>
                    <div className={styles.tooltipDescription}>
                        {tooltip.item.description || "説明なし"}
                    </div>
                    <div className={styles.tooltipStats}>{renderTooltipStats(tooltip.item)}</div>
                </div>
            )}

            {selectedItem && (
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
                            <button
                                type="button"
                                className={`${styles.modalButton} ${styles.yesButton}`}
                                onClick={confirmPurchase}
                            >
                                Yes
                            </button>
                            <button
                                type="button"
                                className={`${styles.modalButton} ${styles.noButton}`}
                                onClick={closeModal}
                            >
                                No
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}