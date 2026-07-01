import styles from "./SearchModal.module.css";
import { useState } from "react";
import { InventoryPanel } from "@/src/components/atoms/panel/InventoryPanel";
import Modal from "../../molecules/Modal";

type Props = {
    setSearchModalOpen: (open: boolean) => void;
    setSearch: (search: string) => void;
}

export default function SearchModal(props: Props) {
    const { setSearchModalOpen, setSearch } = props;
    const [text, setText] = useState<string>("");
    return (
        <Modal setIsModalOpen={setSearchModalOpen}>
            <div onClick={(e) => e.stopPropagation()}>
                <InventoryPanel state="normal" interactive={false} className={styles.searchBox}>
                    <h2 className={styles.searchTitle}>検索</h2>
                    <div className={styles.searchInputRow}>
                        <input
                            type="text"
                            placeholder="アイテム名を入力..."
                            className={styles.searchInput}
                            value={text}
                            onChange={(e) => setText(e.target.value)}
                            autoFocus
                        />
                        <button type="button" className={styles.searchAction} onClick={() => {
                            setSearchModalOpen(false);
                            setSearch(text);
                        }}>
                            検索
                        </button>
                    </div>
                    <button type="button" className={styles.closeAction} onClick={() => setSearchModalOpen(false)}>
                        閉じる
                    </button>
                </InventoryPanel>
            </div>
        </Modal>
    );
}