import type { ReactNode } from "react";
import styles from "./FilterTabs.module.css";
import { InventoryPanel } from "@/src/components/atoms/panel/InventoryPanel";

type Props = {
    tabs: {
        label: string;
        value: string;
        disabled?: boolean;
    }[];
    activeValue: string;
    onChange: (value: string) => void;
    header?: ReactNode;
}

export default function FilterTabs(props: Props){
    const { tabs, activeValue, onChange, header } = props;

    return(
        <InventoryPanel state="normal" interactive={false} className={styles.sidebar}>
            {header &&
                <div>{header}</div>
            }
            
            {tabs.map((tab) => (
                <button 
                    key={tab.value} 
                    type="button"
                    className={`${styles.categoryButton} ${activeValue === tab.value ? styles.active : ""}`} 
                    disabled={tab.disabled} 
                    onClick={() => onChange(tab.value)}
                >
                    {tab.label}
                </button>
            ))}
        </InventoryPanel>
    )
}