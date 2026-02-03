import "../../styles/TemplateRadioCard.css";

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
    <label className={`card ${checked ? "active" : ""} ${className}`}>
      <input
        type="radio"
        name="template"
        value={value}
        checked={checked}
        onChange={() => onChange(value)}
      />

      <img src={imgSrc} alt={title} />

      <div className="info">
        <div className="title">{title}</div>
        <div className="desc">{description}</div>
      </div>
    </label>
  );
}