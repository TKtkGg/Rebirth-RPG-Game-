import { useState, useEffect } from "react";
import { InventoryScreenData } from "./types";
import { ItemScreenData } from "../types/item_types";
import { apiGet, apiPost } from "@/src/lib/apiClient";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { InventoryPanel } from "@/src/components/atoms/panel/InventoryPanel";
import { ReturnButton } from "@/src/components/atoms/button/ReturnButton";
import SearchModal from "@/src/components/Organisms/inventory/SearchModal";
import ItemButton from "@/src/components/Organisms/inventory/ItemButton";
import ItemDetail from "@/src/components/molecules/item/ItemDetail";
import FilterTabs from "@/src/components/Organisms/inventory/FilterTabs";

import styles from "./InventoryScreen.module.css";

type Props = {
    playerId: string;
}

export default function InventoryScreen(props: Props) {
    const { playerId } = props;
    const [data, setData] = useState<InventoryScreenData | null>(null);
    const [itemDetail, setItemDetail] = useState<{ item: ItemScreenData, quantity: number } | null>(null);
    const [category, setCategory] = useState<string>("all");
    const [search, setSearch] = useState<string>("");
    const [searchModalOpen, setSearchModalOpen] = useState(false);
    const router = useRouter();
    useEffect(() => {
        apiGet(`/api/inventory/${playerId}/`).then((data: InventoryScreenData) => {
            setData(data);
        });
    }, [playerId]);

    const rows = data?.inventory_items ?? [];
    const keyword = search.trim().toLowerCase();
    const visible = rows
        .filter((row) => category === "all" || row.item.target === category)
        .filter((row) => row.item.name.toLowerCase().includes(keyword));

    const onSelectItemDetail = (item: ItemScreenData, quantity: number) => {
        setItemDetail({ item, quantity });
    }

    const inventoryTabs = [
        { label: "全て", value: "all" },
        { label: "回復", value: "hp" },
        { label: "魔法", value: "mp" },
    ]

    const handleUseItem = (inventoryItemId: number) => {
        apiPost(`/api/inventory/${playerId}/`, {
            inventory_item_id: inventoryItemId.toString(),
        }).then(() => {
            apiGet(`/api/inventory/${playerId}/`).then((nextData: InventoryScreenData) => {
                setData(nextData);
                if (itemDetail) {
                    const nextSelected = nextData.inventory_items.find((row) => row.id === inventoryItemId);
                    setItemDetail(nextSelected ? { item: nextSelected.item, quantity: nextSelected.quantity } : null);
                }
            });
        });
    };

    return (
        <div className={styles.screen}>
            {searchModalOpen && (
                <SearchModal setSearchModalOpen={setSearchModalOpen} setSearch={setSearch} />
            )}

            <div className={styles.inventoryContainer}>
                <FilterTabs 
                    tabs={inventoryTabs} 
                    activeValue={category} 
                    onChange={(value) => setCategory(value)} 
                    header={
                        <div className={styles.searchIconContainer}>
                            <button type="button" className={styles.searchIconButton} onClick={() => setSearchModalOpen(true)}>
                                <Image src="/game/img/アイコン/検索_アイコン.png" alt="検索" width={48} height={48} />
                            </button>
                            {search && (
                                <button type="button" className={styles.clearSearchButton} onClick={() => {
                                setSearch("");
                                }}>
                                    <Image src="/game/img/アイコン/バツ_アイコン.png" alt="クリア" width={48} height={48} />
                                </button>
                            )}
                        </div>
                    }
                />

                <div className={styles.mainContent}>
                    <InventoryPanel state="normal" interactive={false} className={styles.itemsPanel}>
                        {visible.length === 0 ? (
                            <p className={styles.emptyMessage}>アイテムがありません</p>
                        ) : (
                            visible.map((inventoryItem) => (
                                <ItemButton
                                    key={inventoryItem.id}
                                    inventoryItem={inventoryItem}
                                    onSelectItemDetail={onSelectItemDetail}
                                    handleUseItem={handleUseItem}
                                />
                            ))
                        )}
                    </InventoryPanel>

                    <InventoryPanel state="normal" interactive={false} className={styles.detailPanel}>
                        <ItemDetail itemDetail={itemDetail} />
                    </InventoryPanel>
                </div>
            </div>

            <ReturnButton className={styles.backButton} onClick={() => router.push(`/game/battle/home/${playerId}`)} />
        </div>
    );
}