import styles from './EquipmentButton.module.css';
import Image from 'next/image';
import { EquipmentScreenData } from '@/src/features/types/equipment_types';

type Props = {
    equipment: EquipmentScreenData;
    isEquipped: boolean;
    iconPath: string;
    handleEquip: (equipmentId: string) => void;
    setEquipmentDetail: (equipment: EquipmentScreenData) => void;
}

export default function EquipmentButton(props: Props) {
    const { equipment, isEquipped, iconPath, handleEquip, setEquipmentDetail } = props;

    return (
        <button
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
}