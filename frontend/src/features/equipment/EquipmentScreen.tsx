"use client"

import { useState, useEffect } from "react";
import { apiGet, apiPost } from "../../lib/apiClient";
import { EquipmentChangeScreenData } from "./types";
import { useRouter } from "next/navigation";
import { EquipmentScreenData } from "../types/equipment_types";

type Props = {
    playerId: string;
};

export default function EquipmentScreen(props: Props) {
    const { playerId } = props;
    const [data, setData] = useState<EquipmentChangeScreenData | null>(null);
    const router = useRouter();
    const [tab, setTab] = useState("weapons");
    const [equipmentDetail, setEquipmentDetail] = useState<EquipmentScreenData | null>(null);

    useEffect(() => {
        apiGet(`/api/equipment/${playerId}/`).then((data: EquipmentChangeScreenData) => {
            setData(data);
        });
    }, [playerId]);

    const handleEquip = (equipmentId: string) => {
        apiPost(`/api/equipment/${playerId}/`, {
            equipment_id: equipmentId,
        }).then((data: EquipmentChangeScreenData) => {
            setData(data);
        });
    }

    return (
        <div>
            <button onClick={() => setTab("weapons")}>
                武器
            </button>
            <button onClick={() => setTab("armors")}>
                防具
            </button>

            {tab === "weapons" && data?.owned_weapons.map((weapon) => (
                <button 
                    key={weapon.id} 
                    onClick={() => setEquipmentDetail(weapon)}
                    onDoubleClick={() => handleEquip(weapon.id.toString())}
                >
                    {weapon.name}
                </button>
            ))}
            {tab === "armors" && data?.owned_armors.map((armor) => (
                <button 
                    key={armor.id} 
                    onClick={() => setEquipmentDetail(armor)}
                    onDoubleClick={() => handleEquip(armor.id.toString())}
                >
                    {armor.name}
                </button>
            ))}
            
            {equipmentDetail && (
                <div>
                    <h1>{equipmentDetail.name}</h1>
                    <p>{equipmentDetail.description}</p>
                    <p>ATK: {equipmentDetail.atk_bonus}</p>
                    <p>DEF: {equipmentDetail.def_bonus}</p>
                    <p>SPD: {equipmentDetail.spd_bonus}</p>
                    <p>HP: {equipmentDetail.hp_bonus}</p>
                </div>
            )}

            <button onClick={() => router.push(`/game/battle/home/${playerId}`)}>
                戻る
            </button>
        </div>
    );
}