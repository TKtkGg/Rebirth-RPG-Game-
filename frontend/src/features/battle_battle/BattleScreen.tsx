"use client"

import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { apiGet, apiPost } from "../../lib/apiClient";
import { BattleScreenData } from "./types";
import { ColorButton } from "../../components/atoms/button/ColorButton";
import { MainPanel } from "../../components/atoms/panel/MainPanel";
import styles from "./BattleScreen.module.css";
import { getHpColor, enemyImageSrc, stageBackgroundSrc } from "./battleUtils";
import { MessageBox } from "../../components/molecules/battle/MessageBox";
import { GaugeBar } from "../../components/molecules/battle/GaugeBar";
import { SpecialCommand } from "@/src/components/Organisms/battle/SpecialCommand";

type Props = {
    playerId: string;
    stageId: string;
};

function updateBackgroundFromData(
    data: BattleScreenData,
    setBackgroundImage: (v: string) => void,
) {
    if (data.battle?.stage?.background_image) {
        setBackgroundImage(data.battle.stage.background_image);
    } else if (data.event?.type === "victory" && data.event.payload.stage?.background_image) {
        setBackgroundImage(data.event.payload.stage.background_image);
    }
}

export default function BattleScreen(props: Props) {
    const { playerId, stageId } = props;
    const [data, setData] = useState<BattleScreenData | null>(null);
    const [backgroundImage, setBackgroundImage] = useState<string | null>(null);
    const [itemOpen, setItemOpen] = useState(false);
    const [skillOpen, setSkillOpen] = useState(false);
    const router = useRouter();
    const messageAreaRef = useRef<HTMLDivElement>(null);

    const applyData = useCallback((next: BattleScreenData) => {
        setData(next);
        updateBackgroundFromData(next, setBackgroundImage);
    }, []);

    const loadBattle = () => {
        apiGet(`/api/battle/${playerId}/?stage_id=${stageId}`).then((res: BattleScreenData) => {
            applyData(res);
            setItemOpen(false);
            setSkillOpen(false);
        });
    };

    useEffect(() => {
        loadBattle();
    }, [playerId, stageId]);

    useEffect(() => {
        const el = messageAreaRef.current;
        if (!el) return;
        el.scrollTop = el.scrollHeight;
    }, [data?.battle?.message_history]);

    const handleAttack = () => {
        setItemOpen(false);
        setSkillOpen(false);
        apiPost(`/api/battle/${playerId}/?stage_id=${stageId}`, { action: "attack" }).then(applyData);
    };

    const handleDefend = () => {
        setItemOpen(false);
        setSkillOpen(false);
        apiPost(`/api/battle/${playerId}/?stage_id=${stageId}`, { action: "defend" }).then(applyData);
    };

    const handleEscape = () => {
        setItemOpen(false);
        setSkillOpen(false);
        apiPost(`/api/battle/${playerId}/?stage_id=${stageId}`, { action: "escape" }).then(applyData);
    };

    const handleUseItem = (itemId: string) => {
        setItemOpen(false);
        setSkillOpen(false);
        apiPost(`/api/battle/${playerId}/?stage_id=${stageId}`, { action: "item", item_id: itemId }).then(applyData);
    };

    const handleUseSkill = (index: number) => {
        setItemOpen(false);
        setSkillOpen(false);
        apiPost(`/api/battle/${playerId}/?stage_id=${stageId}`, {
            action: "special",
            special: `skill${index + 1}`,
        }).then(applyData);
    };

    const handleReturn = () => {
        router.push(`/game/battle/home/${playerId}/`);
    };

    const handleContinue = () => {
        loadBattle();
    };

    const battle = data?.battle;
    const enemy = battle?.enemy;
    const showCombat = battle != null && data?.event == null;
    const bgStyle = backgroundImage
        ? { backgroundImage: `url("${stageBackgroundSrc(backgroundImage)}")` }
        : undefined;

    return (
        <div className={styles.battleContainer} style={bgStyle}>
            {!data && <p className={styles.loading}>読み込み中…</p>}

            {showCombat && battle && enemy && (
                <>
                    <div className={styles.messageArea}>
                        <MessageBox message={battle.message_history.join("\n")} />
                    </div>

                    <div className={styles.enemyArea}>
                        <div className={styles.enemyLevel}>LV : {enemy.level}</div>
                        <div
                            className={
                                enemy.is_strong
                                    ? `${styles.enemyName} ${styles.enemyNameStrong}`
                                    : styles.enemyName
                            }
                        >
                            {enemy.name}
                        </div>
                        {enemy.image_url && (
                            <img
                                src={enemyImageSrc(enemy.image_url)}
                                alt={enemy.name}
                                className={styles.enemyImage}
                            />
                        )}
                        <GaugeBar
                            percent={battle.enemy_hp_percent}
                            value={enemy.hp}
                            color={getHpColor}
                            variant="hp"
                            className={styles.enemyHpBarContainer}
                        />
                    </div>

                    <div className={styles.playerArea}>
                        <div
                            className={
                                itemOpen || skillOpen
                                    ? `${styles.playerStatusBox} ${styles.playerStatusBoxWide}`
                                    : styles.playerStatusBox
                            }
                        >
                            {!itemOpen && !skillOpen && (
                                <>
                                    <div className={styles.statusTopRow}>
                                        <div className={styles.playerNameCol}>{battle.player.name}</div>
                                        <div className={styles.statusGauge}>
                                            <span>HP:</span>
                                            <GaugeBar
                                                percent={battle.player_hp_percent}
                                                value={battle.player.total_hp_battle}
                                                color={getHpColor}
                                                variant="hp"
                                                className={styles.statusGaugeBar}
                                            />
                                        </div>
                                        <div className={styles.statusGauge}>
                                            <span>SP:</span>
                                            <GaugeBar
                                                percent={battle.player_sp_percent}
                                                value={battle.player.mp}
                                                variant="sp"
                                                className={styles.statusGaugeBar}
                                            />
                                        </div>
                                    </div>
                                    <div className={styles.statsRow}>
                                        <div className={styles.playerNameCol} />
                                        <div className={styles.statsText}>
                                            ATK:{battle.showplayer_atk} DEF:{battle.showplayer_def}{" "}
                                            SPD:{battle.showplayer_spd}
                                        </div>
                                    </div>
                                    <div className={styles.buttonArea}>
                                        <ColorButton
                                            variant="red"
                                            className={styles.commandButton}
                                            onClick={handleAttack}
                                        >
                                            攻撃
                                        </ColorButton>
                                        <ColorButton
                                            variant="blue"
                                            className={styles.commandButton}
                                            onClick={handleDefend}
                                        >
                                            防御
                                        </ColorButton>
                                        <ColorButton
                                            variant="yellow"
                                            className={styles.commandButton}
                                            onClick={() => {
                                                setItemOpen(false);
                                                setSkillOpen(true);
                                            }}
                                        >
                                            特技
                                        </ColorButton>
                                        <ColorButton
                                            variant="orange"
                                            className={styles.commandButton}
                                            onClick={() => {
                                                setSkillOpen(false);
                                                setItemOpen(true);
                                            }}
                                        >
                                            アイテム
                                        </ColorButton>
                                        <ColorButton
                                            variant="other"
                                            className={styles.commandButton}
                                            onClick={handleEscape}
                                        >
                                            逃げる
                                        </ColorButton>
                                    </div>
                                </>
                            )}

                            {skillOpen && (
                                <SpecialCommand 
                                    mode="skill"
                                    skills={battle.player_skills}
                                    onSelectSkill={handleUseSkill}
                                    onClose={() => setSkillOpen(false)}
                                />
                            )}

                            {itemOpen && (
                                <SpecialCommand
                                    mode="item"
                                    items={battle.player_items}
                                    onSelectItem={handleUseItem}
                                    onClose={() => setItemOpen(false)}
                                />
                            )}
                        </div>
                    </div>
                </>
            )}

            {data?.event?.type === "victory" && (
                <div className={styles.endOverlay}>
                    <MainPanel state="normal" interactive={false} className={styles.endPanel}>
                        <h2 className={styles.endTitle}>勝利</h2>
                        <div
                            className={
                                data.event.payload.newLevel > data.event.payload.existLevel
                                    ? styles.victoryContent
                                    : `${styles.victoryContent} ${styles.victoryContentNoLevelup}`
                            }
                        >
                            <div className={styles.victoryLeft}>
                                <div className={styles.victoryStat}>
                                    <span className={`${styles.victoryLabel} ${styles.expLabel}`}>
                                        EXP
                                    </span>
                                    <span className={styles.victoryValue}>
                                        {data.event.payload.gained_exp}
                                    </span>
                                </div>
                                <div className={styles.victoryStat}>
                                    <span className={`${styles.victoryLabel} ${styles.goldLabel}`}>
                                        GOLD
                                    </span>
                                    <span className={styles.victoryValue}>
                                        {data.event.payload.gained_gold}
                                    </span>
                                </div>
                            </div>
                            {data.event.payload.newLevel > data.event.payload.existLevel && (
                                <div className={styles.victoryRight}>
                                    <div className={styles.victoryLevelup}>レベルアップ！</div>
                                    <div className={styles.victoryLevel}>
                                        LV : {data.event.payload.existLevel} →{" "}
                                        {data.event.payload.newLevel}
                                    </div>
                                </div>
                            )}
                        </div>
                        <div className={styles.endButtons}>
                            <ColorButton
                                variant="other"
                                className={`${styles.endActionButton} ${styles.continueButton}`}
                                onClick={handleContinue}
                            >
                                続けて戦う
                            </ColorButton>
                            <ColorButton
                                variant="other"
                                className={styles.endActionButton}
                                onClick={handleReturn}
                            >
                                戻る
                            </ColorButton>
                        </div>
                    </MainPanel>
                </div>
            )}

            {data?.event?.type === "escape" && (
                <div className={styles.endOverlay}>
                    <MainPanel state="normal" interactive={false} className={styles.endPanel}>
                        <h2 className={styles.endTitle}>逃走</h2>
                        <div className={styles.escapePenalty}>
                            <p>経験値 : -{data.event.payload.exp_penalty}</p>
                            <p>ゴールド : -{data.event.payload.gold_penalty}</p>
                        </div>
                        <div className={styles.endButtons}>
                            <ColorButton
                                variant="other"
                                className={styles.endActionButton}
                                onClick={handleReturn}
                            >
                                戻る
                            </ColorButton>
                        </div>
                    </MainPanel>
                </div>
            )}

            {data?.event?.type === "tohome" && (
                <div className={styles.endOverlay}>
                    <MainPanel state="normal" interactive={false} className={styles.endPanel}>
                        <p className={styles.tohomeMessage}>{data.event.payload.message}</p>
                        <div className={styles.endButtons}>
                            <ColorButton
                                variant="other"
                                className={styles.endActionButton}
                                onClick={handleReturn}
                            >
                                戻る
                            </ColorButton>
                        </div>
                    </MainPanel>
                </div>
            )}
        </div>
    );
}
