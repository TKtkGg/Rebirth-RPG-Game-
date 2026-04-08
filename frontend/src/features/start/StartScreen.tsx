"use client"

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "../../lib/apiClient";
import { useRouter } from "next/navigation";
import { StartScreenData } from "./types";
import styles from "./StartScreen.module.css";

export default function StartScreen() {
    const router = useRouter();
    const [data, setData] = useState<StartScreenData | null>(null);
    const [name, setName] = useState<string>("");
    const [selectedJob, setSelectedJob] = useState<string>("");
    const [errorMessage, setErrorMessage] = useState("");
    useEffect(() => {
        apiGet('/api/start/').then((data: StartScreenData) => {
            setData(data);
            setName(data?.default_name || "");
        }).catch((error: { message: string }) => {
            setErrorMessage(error.message);
        });
    }, []);
    return (
        <div className={styles.startScreen}>
            <div className={styles.startTitle}>職業選択</div>
            <div className={styles.jobForm}>
                <div className={styles.nameRow}>
                    <label htmlFor="start-name" className={styles.nameLabel}>名前</label>
                    <input
                        id="start-name"
                        className={styles.nameInput}
                        type="text"
                        placeholder="冒険者の名前を入力"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                    />
                </div>

                <div className={styles.jobGrid}>
                    {data?.job_slots.map((job: StartScreenData["job_slots"][number], index: number) => (
                        <button
                            key={index}
                            type="button"
                            className={[
                                styles.jobCard,
                                !job.unlocked ? styles.locked : "",
                                selectedJob === job.name ? styles.selected : "",
                            ].join(" ").trim()}
                            onClick={() => setSelectedJob(job.name)}
                            disabled={!job.unlocked}
                            title={job.unlocked ? `${job.description}\n${job.bonus}` : "未開放"}
                        >
                            <img
                                src={`/${job.icon}`}
                                alt={job.name || "未開放"}
                                className={!job.unlocked ? styles.jobIconLocked : styles.jobIcon}
                            />
                            {job.unlocked && <div className={styles.jobName}>{job.name}</div>}
                        </button>
                    ))}
                </div>

                <button
                    className={styles.startButton}
                    onClick={() => {
                if (name === "" && selectedJob === "") {
                    setErrorMessage("名前と職業を選択してください");
                    return;
                }
                else if (name === "") {
                    setErrorMessage("名前を選択してください");
                    return;
                }
                else if (selectedJob === "") {
                    setErrorMessage("職業を選択してください");
                    return;
                }
                apiPost('/api/start/', {
                    name: name,
                    job: selectedJob,
                }).then((data: { player_id: string }) => {
                    const playerId = data.player_id;
                    localStorage.setItem('playerId', playerId)
                    router.push(`/game/battle/home/${playerId}`);
                }).catch((error: { message: string }) => {
                    setErrorMessage(error.message);
                });
                
                    }}
                >
                    冒険を始める
                </button>
                {errorMessage && <p className={styles.errorMessage}>{errorMessage}</p>}
            </div>
        </div>
    )
}