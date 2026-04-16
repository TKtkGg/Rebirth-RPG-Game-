"use client"

import { useEffect } from "react"
import { apiGet, apiPost } from "../../lib/apiClient"
import { ShopScreenData } from "./types"
import { EquipmentScreenData } from "../types/equipment_types"
import { ItemScreenData } from "../types/item_types"
import { useState } from "react"
import { useRouter } from "next/navigation"

type Props = {
    playerId: string;
};

export default function ShopScreen(props: Props) {
    const { playerId } = props;
    const router = useRouter();
    const [data, setData] = useState<ShopScreenData | null>(null);

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
    }

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
    }

    return (
        <div>
            <h1>ショップ</h1>
            {data?.player.name}
            {data?.weapons.map((weapon) => (
                <button 
                    key={weapon.id}
                    onClick={() => handleBuyEquipment(weapon)}
                >
                    {weapon.name} {weapon.price}G
                </button>
            ))}
            {data?.armors.map((armor) => (
                <button 
                    key={armor.id}
                    onClick={() => handleBuyEquipment(armor)}
                >
                    {armor.name} {armor.price}G
                </button>
            ))}
            {data?.items.map((item) => (
                <button 
                    key={item.id}
                    onClick={() => handleBuyItem(item, 1)}
                >
                    {item.name} {item.price}G
                </button>
            ))}
            <button onClick={() => router.push(`/game/battle/home/${playerId}`)}>
                戻る
            </button>
        </div>
    )
}