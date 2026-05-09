"use client"

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "../../lib/apiClient";
import { useRouter } from "next/navigation";
import { StartScreenData } from "./types";
import styles from "./StartScreen.module.css";
import { PrimaryButton } from "@/src/components/atoms/button/PrimaryButton";
import { SectionTitle } from "@/src/components/atoms/title/SectionTitle";
import { MainPanel } from "@/src/components/atoms/panel/MainPanel";

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
            <SectionTitle title="職業選択" />
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
                        <MainPanel 
                            key={index} 
                            state={selectedJob === job.name ? "selected" : job.unlocked ? "normal" : "muted"}
                            interactive={job.unlocked}
                            as="button"
                            className={styles.jobCardSize}
                            onClick={() => setSelectedJob(job.name)}
                            disabled={!job.unlocked}
                        >
                            <img
                                src={`${job.icon}`}
                                alt={job.name || "未開放"}
                                className={!job.unlocked ? styles.jobIconLocked : styles.jobIcon}
                            />
                            {job.unlocked && <div className={styles.jobName}>{job.name}</div>} 
                        </MainPanel>
                    ))}
                </div>

                <PrimaryButton
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
                </PrimaryButton>
                {errorMessage && <p className={styles.errorMessage}>{errorMessage}</p>}
            </div>
        </div>
    )
}