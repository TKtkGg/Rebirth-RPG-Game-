"use client"

import { useState, useEffect } from "react";
import { apiGet, apiPost } from "../../lib/apiClient";
import { EquipmentChangeScreenData } from "./types";
import { useRouter } from "next/navigation";
import { EquipmentScreenData } from "../types/equipment_types";
import styles from "./EquipmentScreen.module.css";
import { ReturnButton } from "@/src/components/atoms/button/ReturnButton";
import DetailRow from "@/src/components/atoms/row/DetailRow";
import StatusChangeRow from "@/src/components/atoms/row/StatusChangeRow";
import EquipmentButton from "@/src/components/Organisms/inventory/EquipmentButton";
import { InventoryPanel } from "@/src/components/atoms/panel/InventoryPanel";
import FilterTabs from "@/src/components/Organisms/inventory/FilterTabs";

type Props = {
    playerId: string;
};

export default function EquipmentScreen(props: Props) {
    const { playerId } = props;
    const [data, setData] = useState<EquipmentChangeScreenData | null>(null);
    const router = useRouter();
    const [tab, setTab] = useState<"weapons" | "armors">("weapons");
    const [equipmentDetail, setEquipmentDetail] = useState<EquipmentScreenData | null>(null);

    const equipmentTabs = [
        { label: "武器", value: "weapons" },
        { label: "防具", value: "armors" },
    ];

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
    };

    const selectedList = tab === "weapons" ? data?.owned_weapons ?? [] : data?.owned_armors ?? [];
    const currentEquippedId = tab === "weapons" ? data?.current_weapon?.id : data?.current_armor?.id;

    const formatBonus = (value: number) => {
        if (value > 0) {
            return `+${value}`;
        }
        if (value < 0) {
            return `${value}`;
        }
        return "0";
    };

    const previewStats = (() => {
        if (!data || !equipmentDetail) {
            return null;
        }

        const isWeapon = equipmentDetail.equipment_type === "weapon";
        const isEquipped = isWeapon
            ? data.current_weapon?.id === equipmentDetail.id
            : data.current_armor?.id === equipmentDetail.id;

        if (isEquipped) {
            return null;
        }

        const currentWeapon = {
            atk: data.current_weapon?.atk_bonus ?? 0,
            def: data.current_weapon?.def_bonus ?? 0,
            spd: data.current_weapon?.spd_bonus ?? 0,
            hp: data.current_weapon?.hp_bonus ?? 0,
        };
        const currentArmor = {
            atk: data.current_armor?.atk_bonus ?? 0,
            def: data.current_armor?.def_bonus ?? 0,
            spd: data.current_armor?.spd_bonus ?? 0,
            hp: data.current_armor?.hp_bonus ?? 0,
        };

        const nextTotals = isWeapon
            ? {
                atk: data.base_stats.atk + equipmentDetail.atk_bonus + currentArmor.atk,
                def: data.base_stats.def + equipmentDetail.def_bonus + currentArmor.def,
                spd: data.base_stats.spd + equipmentDetail.spd_bonus + currentArmor.spd,
                max_hp: data.base_stats.max_hp + equipmentDetail.hp_bonus + currentArmor.hp,
            }
            : {
                atk: data.base_stats.atk + currentWeapon.atk + equipmentDetail.atk_bonus,
                def: data.base_stats.def + currentWeapon.def + equipmentDetail.def_bonus,
                spd: data.base_stats.spd + currentWeapon.spd + equipmentDetail.spd_bonus,
                max_hp: data.base_stats.max_hp + currentWeapon.hp + equipmentDetail.hp_bonus,
            };

        return {
            hp: {
                old: data.current_totals.max_hp,
                next: nextTotals.max_hp,
                diff: nextTotals.max_hp - data.current_totals.max_hp,
            },
            atk: {
                old: data.current_totals.atk,
                next: nextTotals.atk,
                diff: nextTotals.atk - data.current_totals.atk,
            },
            def: {
                old: data.current_totals.def,
                next: nextTotals.def,
                diff: nextTotals.def - data.current_totals.def,
            },
            spd: {
                old: data.current_totals.spd,
                next: nextTotals.spd,
                diff: nextTotals.spd - data.current_totals.spd,
            },
        };
    })();

    const formatChange = (oldValue: number, nextValue: number, diff: number) => {
        const diffLabel = diff > 0 ? `+${diff}` : diff < 0 ? `${diff}` : "±0";
        return `${oldValue}→${nextValue} (${diffLabel})`;
    };

    return (
        <div className={styles.container}>
            <FilterTabs 
                tabs={equipmentTabs} 
                activeValue={tab} 
                onChange={(value) => {
                    setTab(value as "weapons" | "armors");
                    setEquipmentDetail(null);
                }}
            />

            <div className={styles.mainContent}>
                <InventoryPanel state="normal" interactive={false} as="div" className={styles.equipmentListPanel}>
                    <div className={styles.equipmentGrid}>
                        {selectedList.length === 0 && (
                            <div className={styles.noEquipment}>
                                所持している{tab === "weapons" ? "武器" : "防具"}がありません
                            </div>
                        )}
                        {selectedList.map((equipment) => {
                            const isEquipped = currentEquippedId === equipment.id;
                            const iconPath =
                                equipment.equipment_type === "weapon"
                                    ? "/game/img/アイコン/武器_アイコン.png"
                                    : "/game/img/アイコン/防具_アイコン.png";

                            return (
                                <EquipmentButton
                                    key={equipment.id}
                                    equipment={equipment}
                                    isEquipped={isEquipped}
                                    iconPath={iconPath}
                                    handleEquip={handleEquip}
                                    setEquipmentDetail={setEquipmentDetail}
                                />
                            );
                        })}
                    </div>
                </InventoryPanel>

                <InventoryPanel state="normal" interactive={false} as="div" className={styles.detailPanel}>
                    <div className={styles.detailTitle}>{equipmentDetail?.name ?? "-"}</div>
                    <div className={styles.detailSection}>
                        <div className={styles.detailSectionTitle}>能力上昇</div>
                        <div className={styles.detailStats}>
                            <DetailRow label="HP" value={equipmentDetail ? formatBonus(equipmentDetail.hp_bonus) : "-"} />
                            <DetailRow label="ATK" value={equipmentDetail ? formatBonus(equipmentDetail.atk_bonus) : "-"} />
                            <DetailRow label="DEF" value={equipmentDetail ? formatBonus(equipmentDetail.def_bonus) : "-"} />
                            <DetailRow label="SPD" value={equipmentDetail ? formatBonus(equipmentDetail.spd_bonus) : "-"} />
                        </div>
                    </div>
                    <div className={styles.detailSection}>
                        <div className={styles.detailSectionTitle}>解説</div>
                        <div className={styles.detailContent}>
                            {equipmentDetail?.description ?? "装備を選択してください"}
                        </div>
                    </div>
                </InventoryPanel>

                <InventoryPanel state="normal" interactive={false} as="div" className={styles.statsPanel}>
                    <StatusChangeRow label="HP" value={data?.current_totals.max_hp ?? "-"} changeText={previewStats ? formatChange(previewStats.hp.old, previewStats.hp.next, previewStats.hp.diff) : ""} />
                    <StatusChangeRow label="ATK" value={data?.current_totals.atk ?? "-"} changeText={previewStats ? formatChange(previewStats.atk.old, previewStats.atk.next, previewStats.atk.diff) : ""} />
                    <StatusChangeRow label="DEF" value={data?.current_totals.def ?? "-"} changeText={previewStats ? formatChange(previewStats.def.old, previewStats.def.next, previewStats.def.diff) : ""} />
                    <StatusChangeRow label="SPD" value={data?.current_totals.spd ?? "-"} changeText={previewStats ? formatChange(previewStats.spd.old, previewStats.spd.next, previewStats.spd.diff) : ""} />
                </InventoryPanel>
            </div>

            <ReturnButton className={styles.backButton} onClick={() => router.push(`/game/battle/home/${playerId}`)} />
        </div>
    );
}