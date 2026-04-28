import { useState, useEffect } from "react";
import { InventoryScreenData } from "./types";
import { ItemScreenData } from "../types/item_types";
import { apiGet, apiPost } from "@/src/lib/apiClient";
import { useRouter } from "next/navigation";

type Props = {
    playerId: string;
}

export default function InventoryScreen(props: Props) {
    const { playerId } = props;
    const [data, setData] = useState<InventoryScreenData | null>(null);
    const [itemDetail, setItemDetail] = useState<{ item: ItemScreenData, quantity: number } | null>(null);
    const [category, setCategory] = useState<string>("all");
    const [search, setSearch] = useState<string>("");
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

    return (
        <div>
            <input type="text" placeholder="アイテム名を検索" value={search} onChange={(e) => setSearch(e.target.value)} />
            <button onClick={() => setSearch("")}>クリア</button>
            <button onClick={() => setCategory("all")}>All</button>
            <button onClick={() => setCategory("hp")}>HP</button>
            <button onClick={() => setCategory("mp")}>MP</button>

            {visible.map((item: { id: number; item: ItemScreenData; quantity: number }) => (
                <button 
                    key={item.id} 
                    onClick={() => setItemDetail({ item: item.item, quantity: item.quantity })}
                    onDoubleClick={() => apiPost(`/api/inventory/${playerId}/`, {
                        inventory_item_id: item.id.toString() 
                    }).then(() => {
                        apiGet(`/api/inventory/${playerId}/`).then((data: InventoryScreenData) => {
                            setData(data);
                            setItemDetail({ item: item.item, quantity: item.quantity - 1 });
                        });
                    })}
                >
                    {item.item.name}
                </button>
            ))}

            {itemDetail && (
                <div>
                    <h1>{itemDetail.item.name}</h1>
                    <p>{itemDetail.item.description}</p>
                    <p>{itemDetail.item.target}</p>
                    <p>{itemDetail.item.effect_amount}</p>
                    <p>{itemDetail.quantity}</p>
                </div>
            )}
            <button onClick={() => router.push(`/game/battle/home/${playerId}`)}>戻る</button>
        </div>
    );
}