import styles from "./BattleEndPanel.module.css";
import { BattleEvent } from "@/src/features/battle_battle/event_types";
import { MainPanel } from "../../atoms/panel/MainPanel";
import { ColorButton } from "../../atoms/button/ColorButton";

type Props = {
    event: BattleEvent;
    onReturn: () => void;
    onContinue?: () => void;
}

export const BattleEndPanel = (props: Props) => {
    const { event, onReturn, onContinue } = props;

    return (
        <div className={styles.endOverlay}>
            <MainPanel state="normal" interactive={false} className={styles.endPanel}>
                {event.type === "victory" && (
                    <>
                        <h2 className={styles.endTitle}>勝利</h2>
                        <div
                            className={
                                event.payload.newLevel > event.payload.existLevel
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
                                        {event.payload.gained_exp}
                                    </span>
                                </div>
                                <div className={styles.victoryStat}>
                                    <span className={`${styles.victoryLabel} ${styles.goldLabel}`}>
                                        GOLD
                                    </span>
                                    <span className={styles.victoryValue}>
                                        {event.payload.gained_gold}
                                    </span>
                                </div>
                            </div>
                            {event.payload.newLevel > event.payload.existLevel && (
                                <div className={styles.victoryRight}>
                                    <div className={styles.victoryLevelup}>レベルアップ！</div>
                                    <div className={styles.victoryLevel}>
                                        LV : {event.payload.existLevel} →{" "}
                                        {event.payload.newLevel}
                                    </div>
                                </div>
                            )}
                        </div>
                        <div className={styles.endButtons}>
                            <ColorButton
                                variant="other"
                                className={`${styles.endActionButton} ${styles.continueButton}`}
                                onClick={onContinue ?? onReturn}
                            >
                                続けて戦う
                            </ColorButton>
                            <ColorButton
                                variant="other"
                                className={styles.endActionButton}
                                onClick={onReturn}
                            >
                                戻る
                            </ColorButton>
                        </div>
                    </>
                )}
                {event.type === "escape" && (
                    <>
                        <h2 className={styles.endTitle}>逃走</h2>
                        <div className={styles.escapePenalty}>
                            <p>経験値 : -{event.payload.exp_penalty}</p>
                            <p>ゴールド : -{event.payload.gold_penalty}</p>
                        </div>
                        <div className={styles.endButtons}>
                            <ColorButton
                                variant="other"
                                className={styles.endActionButton}
                                onClick={onReturn}
                            >
                                戻る
                            </ColorButton>
                        </div>
                    </>
                )}
                {event.type === "tohome" && (
                    <>
                        <p className={styles.tohomeMessage}>{event.payload.message}</p>
                        <div className={styles.endButtons}>
                            <ColorButton
                                variant="other"
                                className={styles.endActionButton}
                                onClick={onReturn}
                            >
                                戻る
                            </ColorButton>
                        </div>
                    </>
                )}
                {event.type === "gameover" && (
                    <>
                        <h2 className={styles.endTitle}>ゲームオーバー</h2>
                        <div className={styles.endButtons}>
                            <ColorButton 
                                variant="other" 
                                className={styles.endActionButton} 
                                onClick={onReturn}
                            >
                                戻る
                            </ColorButton>
                        </div>
                    </>
                )}
            </MainPanel>
        </div>
    )
}