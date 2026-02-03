import styles from "../../styles/TemplateRadioCard.module.css";

export default function TemplateRadioCard({
  value,
  checked,
  onChange,
  imgSrc,
  title,
  description,
  className = "",
}) {
  return (
    <label className={`${styles.card} ${checked ? styles.active : ""} ${className}`}>
      <input
        type="radio"
        name="template"
        value={value}
        checked={checked}
        onChange={() => onChange(value)}
      />

      <img src={imgSrc} alt={title} />

      <div className={styles.info}>
        <div className={styles.title}>{title}</div>
        <div className={styles.desc}>{description}</div>
      </div>
    </label>
  );
}