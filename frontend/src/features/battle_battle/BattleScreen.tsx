"use client"

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { apiGet, apiPost } from "../../lib/apiClient";
import { BattleScreenData } from "./types";

type Props = {
    playerId: string;
    stageId: string;
};

export default function BattleScreen(props: Props) {
    const { playerId, stageId } = props;
    const [data, setData] = useState<BattleScreenData | null>(null);
    const [itemOpen, setItemOpen] = useState(false);
    const [skillOpen, setSkillOpen] = useState(false);
    const router = useRouter();

    useEffect(() => {
        apiGet(`/api/battle/${playerId}/?stage_id=${stageId}`).then((data: BattleScreenData) => {
            setData(data);
        });
    }, [playerId, stageId]);

    const handleAttack = () => {
        setItemOpen(false);
        setSkillOpen(false);
        apiPost(`/api/battle/${playerId}/?stage_id=${stageId}`, { action: "attack" }).then((data: BattleScreenData) => {
            setData(data);
        });
    }

    const handleDefend = () => {
        setItemOpen(false);
        setSkillOpen(false);
        apiPost(`/api/battle/${playerId}/?stage_id=${stageId}`, { action: "defend" }).then((data: BattleScreenData) => {
            setData(data);
        });
    }

    const handleEscape = () => {
        setItemOpen(false);
        setSkillOpen(false);
        apiPost(`/api/battle/${playerId}/?stage_id=${stageId}`, { action: "escape" }).then((data: BattleScreenData) => {
            setData(data);
        });
    }

    const handleUseItem = (itemId: string) => {
        setItemOpen(false);
        setSkillOpen(false);
        apiPost(`/api/battle/${playerId}/?stage_id=${stageId}`, { action: "item", item_id: itemId }).then((data: BattleScreenData) => {
            setData(data);
        });
    }

    const handleUseSkill = (index: number) => {
        setItemOpen(false);
        setSkillOpen(false);
        apiPost(`/api/battle/${playerId}/?stage_id=${stageId}`, { action: "special", special: `skill${index + 1}` }).then((data: BattleScreenData) => {
            setData(data);
        });
        setSkillOpen(false);
    }

    const handleReturn = () => {
        router.push(`/game/battle/home/${playerId}/`);
    }

    return (
        <div>
            {data?.battle !== null && (
                <>
                    <p>{data?.battle?.message_history.join("\n")}</p>
                    <p>{data?.battle?.player.name} vs {data?.battle?.enemy?.name}</p>
                    <p>{data?.battle?.enemy?.hp} / {data?.battle?.enemy?.max_hp} ({data?.battle?.enemy_hp_percent}%)</p>
                    <p>{data?.battle?.enemy?.atk}</p>
                    <p>{data?.battle?.enemy?.defense}</p>
                    <p>{data?.battle?.enemy?.spd}</p>
                    <br />
                    <p>{data?.battle?.player.total_hp_battle} / {data?.battle?.player.total_max_hp_battle} ({data?.battle?.player_hp_percent}%)</p>
                    <p>{data?.battle?.player.mp} / {data?.battle?.player.max_mp} ({data?.battle?.player_sp_percent}%)</p>
                    <p>{data?.battle?.player.total_atk_battle}</p>
                    <p>{data?.battle?.player.total_def_battle}</p>
                    <p>{data?.battle?.player.total_spd_battle}</p>
                    <br />
                    <button onClick={handleAttack}>攻撃</button>
                    <button onClick={handleDefend}>防御</button>
                    <button onClick={() => setSkillOpen(true)}>特技</button>
                    <button onClick={() => setItemOpen(true)}>アイテム</button>
                    <button onClick={handleEscape}>逃げる</button>
                    {itemOpen && (
                        <div>
                            <p>アイテム</p>
                            {data?.battle?.player_items.map((item) => (
                                <button key={item.id} onClick={() => handleUseItem(item.item.id.toString())}>{item.item.name} (×{item.quantity})</button>
                            ))}
                            <button onClick={() => setItemOpen(false)}>閉じる</button>
                        </div>
                    )}
                    {skillOpen && (
                        <div>
                            <p>特技</p>
                            {data?.battle?.player_skills.map((skill, index) => (
                                <button key={index} onClick={() => handleUseSkill(index)}>{skill.name} (SP: {skill.cost})</button>
                            ))}
                            <button onClick={() => setSkillOpen(false)}>閉じる</button>
                        </div>
                    )}
                </>
            )}
            

            {data?.event?.type === "victory" && (
                <div>
                    <p>勝利</p>
                    <p>EXP: +{data?.event?.payload.gained_exp}</p>
                    <p>GOLD: +{data?.event?.payload.gained_gold}</p>
                    {data?.event?.payload.newLevel > data?.event?.payload.existLevel && (
                        <>
                            <p>レベルアップ！</p>
                            <p>LV: {data?.event?.payload.existLevel} → {data?.event?.payload.newLevel}</p>
                        </>
                    )}
                    <button onClick={handleReturn}>戻る</button>
                </div>
            )}

            {data?.event?.type === "escape" && (
                <div>
                    <p>{data?.event?.payload.message}</p>
                    <p>EXP: -{data?.event?.payload.exp_penalty}</p>
                    <p>GOLD: -{data?.event?.payload.gold_penalty}</p>
                    <button onClick={handleReturn}>戻る</button>
                </div>
            )}

            {data?.event?.type === "tohome" && (
                <div>
                    <p>{data?.event?.payload.message}</p>
                    <button onClick={handleReturn}>戻る</button>
                </div>
            )}
        </div>
    );
}