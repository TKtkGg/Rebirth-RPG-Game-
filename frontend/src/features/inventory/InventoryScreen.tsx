import { useState, useEffect } from "react";
import { InventoryScreenData } from "./types";
import { ItemScreenData } from "../types/item_types";
import { apiGet, apiPost } from "@/src/lib/apiClient";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { InventoryPanel } from "@/src/components/atoms/panel/InventoryPanel";
import { ReturnButton } from "@/src/components/atoms/button/ReturnButton";
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
                <div className={styles.searchOverlay} onClick={() => setSearchModalOpen(false)}>
                    <InventoryPanel state="normal" interactive={false} className={styles.searchBox}>
                        <h2 className={styles.searchTitle}>アイテム検索</h2>
                        <div className={styles.searchInputRow} onClick={(e) => e.stopPropagation()}>
                            <input
                                type="text"
                                placeholder="アイテム名を入力..."
                                className={styles.searchInput}
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                autoFocus
                            />
                            <button type="button" className={styles.searchAction} onClick={() => setSearchModalOpen(false)}>
                                検索
                            </button>
                        </div>
                        <button type="button" className={styles.closeAction} onClick={() => setSearchModalOpen(false)}>
                            閉じる
                        </button>
                    </InventoryPanel>
                </div>
            )}

            <div className={styles.inventoryContainer}>
                <InventoryPanel state="normal" interactive={false} className={styles.sidebar}>
                    <button type="button" className={styles.searchIconButton} onClick={() => setSearchModalOpen(true)}>
                        <Image src="/game/img/アイコン/検索_アイコン.png" alt="検索" width={48} height={48} />
                    </button>

                    <button type="button" className={`${styles.categoryButton} ${category === "all" ? styles.active : ""}`} onClick={() => setCategory("all")}>全て</button>
                    <button type="button" className={`${styles.categoryButton} ${category === "hp" ? styles.active : ""}`} onClick={() => setCategory("hp")}>回復</button>
                    <button type="button" className={styles.categoryButton}>未定</button>
                    <button type="button" className={styles.categoryButton}>未定</button>
                    <button type="button" className={styles.categoryButton}>未定</button>
                </InventoryPanel>

                <div className={styles.mainContent}>
                    <InventoryPanel state="normal" interactive={false} className={styles.itemsPanel}>
                        {visible.length === 0 ? (
                            <p className={styles.emptyMessage}>アイテムがありません</p>
                        ) : (
                            visible.map((inventoryItem) => (
                                <InventoryPanel
                                    key={inventoryItem.id}
                                    state={itemDetail?.item.id === inventoryItem.item.id ? "selected" : "normal"}
                                    interactive
                                    as="button"
                                    className={styles.itemCard}
                                    onClick={() => setItemDetail({ item: inventoryItem.item, quantity: inventoryItem.quantity })}
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
                                </InventoryPanel>
                            ))
                        )}
                    </InventoryPanel>

                    <InventoryPanel state="normal" interactive={false} className={styles.detailPanel}>
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
                    </InventoryPanel>
                </div>
            </div>

            <ReturnButton className={styles.backButton} onClick={() => router.push(`/game/battle/home/${playerId}`)} />
        </div>
    );
}