"use client"

import { useEffect, useMemo, useState } from "react";
import { apiGet, apiPost } from "../../lib/apiClient";
import { ShopScreenData } from "./types";
import { EquipmentScreenData } from "../types/equipment_types";
import { ItemScreenData } from "../types/item_types";
import { useRouter } from "next/navigation";
import { SectionTitle } from "@/src/components/atoms/title/SectionTitle";
import { ReturnButton } from "@/src/components/atoms/button/ReturnButton";
import styles from "./ShopScreen.module.css";
import { Tooltip } from "@/src/components/Organisms/shop/Tooltip";
import { ShopModal } from "@/src/components/Organisms/shop/ShopModal";
import { MerchandiseButton } from "@/src/components/Organisms/shop/MerchandiseButton";
import { ShopDisplayItem } from "./types";

type Props = {
    playerId: string;
};

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
    const [isModalOpen, setIsModalOpen] = useState(false);

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
        setIsModalOpen(true);
    };

    const handleTooltipEnter = (item: ShopDisplayItem, x: number, y: number) => {
        setTooltip({ item, x, y });
    };

    const handleTooltipMove = (x: number, y: number) => {
        setTooltip((prev) => prev ? { ...prev, x, y } : null);
    };

    const handleTooltipLeave = () => {
        setTooltip(null);
    };

    const confirmPurchase = (purchaseQuantity: number) => {
        if (!selectedItem) {
            return;
        }

        if (selectedItem.type === "item") {
            handleBuyItem(selectedItem, purchaseQuantity);
        } else {
            handleBuyEquipment(selectedItem);
        }
        setIsModalOpen(false);
    };

    return (
        <div className={`${styles.shopContainer} ${isModalOpen ? styles.dimmed : ""}`}>
            <SectionTitle title="ショップ" className={styles.title} />
            <div className={styles.shopGrid}>
                {displayItems.map((item) => (
                    <MerchandiseButton
                        key={`${item.type}-${item.id}`}
                        item={item}
                        onSelectItem={handleItemClick}
                        onTooltipEnter={handleTooltipEnter}
                        onTooltipMove={handleTooltipMove}
                        onTooltipLeave={handleTooltipLeave}
                    />
                ))}
            </div>

            <ReturnButton
                className={styles.backButton}
                onClick={() => router.push(`/game/battle/home/${playerId}`)}
            />

            {tooltip && (
                <Tooltip tooltip={tooltip} />
            )}

            {isModalOpen && selectedItem && (
                <ShopModal
                    setIsModalOpen={setIsModalOpen}
                    confirmPurchase={confirmPurchase}
                    selectedItem={selectedItem}
                    data={data}
                />
            )}
        </div>
    );
}