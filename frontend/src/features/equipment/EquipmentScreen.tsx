"use client"

import { useState, useEffect } from "react";
import { apiGet, apiPost } from "../../lib/apiClient";
import { EquipmentChangeScreenData } from "./types";
import { useRouter } from "next/navigation";
import { EquipmentScreenData } from "../types/equipment_types";
import Image from "next/image";
import styles from "./EquipmentScreen.module.css";
import { ReturnButton } from "@/src/components/atoms/button/ReturnButton";

type Props = {
    playerId: string;
};

export default function EquipmentScreen(props: Props) {
    const { playerId } = props;
    const [data, setData] = useState<EquipmentChangeScreenData | null>(null);
    const router = useRouter();
    const [tab, setTab] = useState<"weapons" | "armors">("weapons");
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
            <div className={styles.sidebar}>
                <button
                    type="button"
                    className={`${styles.sidebarItem} ${tab === "weapons" ? styles.active : ""}`}
                    onClick={() => {
                        setTab("weapons");
                        setEquipmentDetail(null);
                    }}
                >
                    武器
                </button>
                <button
                    type="button"
                    className={`${styles.sidebarItem} ${tab === "armors" ? styles.active : ""}`}
                    onClick={() => {
                        setTab("armors");
                        setEquipmentDetail(null);
                    }}
                >
                    防具
                </button>
            </div>

            <div className={styles.mainContent}>
                <div className={styles.equipmentListPanel}>
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
                                <button
                                    key={equipment.id}
                                    type="button"
                                    className={`${styles.equipmentItem} ${isEquipped ? styles.equipped : ""}`}
                                    onClick={() => setEquipmentDetail(equipment)}
                                    onDoubleClick={() => !isEquipped && handleEquip(equipment.id.toString())}
                                >
                                    <Image
                                        src={iconPath}
                                        alt={equipment.name}
                                        width={80}
                                        height={80}
                                        className={styles.equipmentIcon}
                                    />
                                    <div className={styles.equipmentName}>{equipment.name}</div>
                                </button>
                            );
                        })}
                    </div>
                </div>

                <div className={styles.detailPanel}>
                    <div className={styles.detailTitle}>{equipmentDetail?.name ?? "-"}</div>
                    <div className={styles.detailSection}>
                        <div className={styles.detailSectionTitle}>能力上昇</div>
                        <div className={styles.detailStats}>
                            <div className={styles.detailStatItem}>
                                <span>HP:</span>
                                <span>{equipmentDetail ? formatBonus(equipmentDetail.hp_bonus) : "-"}</span>
                            </div>
                            <div className={styles.detailStatItem}>
                                <span>ATK:</span>
                                <span>{equipmentDetail ? formatBonus(equipmentDetail.atk_bonus) : "-"}</span>
                            </div>
                            <div className={styles.detailStatItem}>
                                <span>DEF:</span>
                                <span>{equipmentDetail ? formatBonus(equipmentDetail.def_bonus) : "-"}</span>
                            </div>
                            <div className={styles.detailStatItem}>
                                <span>SPD:</span>
                                <span>{equipmentDetail ? formatBonus(equipmentDetail.spd_bonus) : "-"}</span>
                            </div>
                        </div>
                    </div>
                    <div className={styles.detailSection}>
                        <div className={styles.detailSectionTitle}>解説</div>
                        <div className={styles.detailContent}>
                            {equipmentDetail?.description ?? "装備を選択してください"}
                        </div>
                    </div>
                </div>

                <div className={styles.statsPanel}>
                    <div className={styles.statItem}>
                        <span className={styles.statLabel}>HP:</span>
                        <div className={styles.statValueBlock}>
                            <div className={styles.statValue}>{data?.current_totals.max_hp ?? "-"}</div>
                            <div className={styles.statChange}>
                                {previewStats ? formatChange(previewStats.hp.old, previewStats.hp.next, previewStats.hp.diff) : ""}
                            </div>
                        </div>
                    </div>
                    <div className={styles.statItem}>
                        <span className={styles.statLabel}>ATK:</span>
                        <div className={styles.statValueBlock}>
                            <div className={styles.statValue}>{data?.current_totals.atk ?? "-"}</div>
                            <div className={styles.statChange}>
                                {previewStats ? formatChange(previewStats.atk.old, previewStats.atk.next, previewStats.atk.diff) : ""}
                            </div>
                        </div>
                    </div>
                    <div className={styles.statItem}>
                        <span className={styles.statLabel}>DEF:</span>
                        <div className={styles.statValueBlock}>
                            <div className={styles.statValue}>{data?.current_totals.def ?? "-"}</div>
                            <div className={styles.statChange}>
                                {previewStats ? formatChange(previewStats.def.old, previewStats.def.next, previewStats.def.diff) : ""}
                            </div>
                        </div>
                    </div>
                    <div className={styles.statItem}>
                        <span className={styles.statLabel}>SPD:</span>
                        <div className={styles.statValueBlock}>
                            <div className={styles.statValue}>{data?.current_totals.spd ?? "-"}</div>
                            <div className={styles.statChange}>
                                {previewStats ? formatChange(previewStats.spd.old, previewStats.spd.next, previewStats.spd.diff) : ""}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <ReturnButton className={styles.backButton} onClick={() => router.push(`/game/battle/home/${playerId}`)} />
        </div>
    );
}