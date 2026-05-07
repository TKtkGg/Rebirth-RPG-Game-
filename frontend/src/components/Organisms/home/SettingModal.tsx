import Modal from "../../molecules/Modal";
import styles from "./SettingModal.module.css";
import { ColorButton } from "../../atoms/button/ColorButton";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiPost } from "@/src/lib/apiClient";

type Props = {
    setIsModalOpen: (open: boolean) => void;
}

export function SettingModal(props: Props) {
    const { setIsModalOpen } = props;
    const [errorMessage, setErrorMessage] = useState("");
    const router = useRouter();
    return (
        <Modal
            setIsModalOpen={setIsModalOpen}
        >
            <div
                className={styles.settingsModal}
                role="dialog"
                aria-modal="true"
                aria-label="オプション"
                onClick={(e) => e.stopPropagation()}
            >
                <button
                    type="button"
                    className={styles.modalClose}
                    aria-label="閉じる"
                    onClick={() => setIsModalOpen(false)}
                >
                    &times;
                </button>
                <div className={styles.modalTitle}>オプション</div>
                <div className={styles.modalOptions}>
                    <ColorButton 
                        variant="blue" 
                        disabled 
                        onClick={() => {}}
                        className={styles.modalOption}
                    >
                        設定
                    </ColorButton>
                    <ColorButton
                        variant="brown"
                        onClick={() => {
                            setErrorMessage("");
                            apiPost(`/api/auth/logout/`, {})
                                .then((d: { ok: boolean }) => {
                                    if (d.ok) {
                                        localStorage.removeItem("playerId");
                                        router.push("/auth/");
                                    }
                                })
                                .catch((error: { message: string }) => {
                                    setErrorMessage(error.message);
                                });
                        }}
                        className={styles.modalOption}
                    >
                        ログアウトしてタイトルに戻る
                    </ColorButton>
                    <ColorButton 
                        variant="red" 
                        onClick={() => setIsModalOpen(false)} 
                        className={styles.modalOption}
                    >
                        ゲームに戻る
                    </ColorButton>
                </div>
                {errorMessage ? <p className={styles.modalError}>{errorMessage}</p> : null}
            </div>
        </Modal>
    );
}