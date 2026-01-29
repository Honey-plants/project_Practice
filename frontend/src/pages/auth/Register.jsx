import "../../styles/Register.css";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Modal from "../../components/common/Modal";
import { COUNTRY_OPTIONS, GENDER } from "../../contents/register";
import { MemberAPI } from "../../api/memberApi";

/* 정규식 */
const REGEX = {
  email: /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/,
  password: /^.{8,20}$/,
};

function validate(formData) {
  const errors = {};
  const email = formData.email.trim();

  if (!email) errors.email = "Email is required.";
  else if (!REGEX.email.test(email)) errors.email = "Invalid email format.";

  if (!formData.password) {
    errors.password = "Password is required.";
  } else if (!REGEX.password.test(formData.password)) {
    errors.password = "Password must be 8~20 characters.";
  }

  if (formData.password !== formData.passwordConfirm) {
    errors.passwordConfirm = "Password does not match.";
  }

  return errors;
}

export default function Register() {
  const nav = useNavigate();

  const [formData, setFormData] = useState({
    email: "",
    password: "",
    passwordConfirm: "",
    gender: "",
    country: "",
  });

  const [modalType, setModalType] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const onChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const submitRegister = async () => {
    const errors = validate(formData);
    if (Object.keys(errors).length > 0) {
      alert(Object.values(errors).join("\n"));
      return false;
    }

    const payload = {
      email: formData.email.trim(),
      password: formData.password,
      nickname: formData.nickname,
      gender: formData.gender || null,
      country: formData.country || null,
    };
    console.log("payload :: ", payload)
    try {
      await MemberAPI.register(payload);
      alert("Register complete!");
      return true;
    } catch (e) {
      console.error(e);
      alert(e?.response?.data?.message || "Register failed");
      return false;
    }
  };
  // Admin 등록 한 Category, Item 리스트 조회
  const { stateMeta } = useContext(MetaContext);

  useEffect(() => {
    (async () => {
      try {
        const r = await MemberAPI.getCategoriesWithItems();
        // 기대 형태: [{category_id, category_label_ko, items:[{item_id, item_label_ko}]}]
        setCategories(Array.isArray(r.data) ? r.data : r.data?.items ?? []);
      } catch (e) {
        setError(e.message || "카테고리/아이템 조회 실패");
      }
    })();
  }, []);

  const openModal = (type) => {
    setModalType(type);
    setIsModalOpen(true);
  };

  const handleConfirm = async () => {
    if (modalType === "cancel") {
      setIsModalOpen(false);
      nav("/");
      return;
    }

    if (modalType === "Register") {
      const ok = await submitRegister();
      if (ok) nav("/");
      setIsModalOpen(false);
    }
  };

  return (
    <div className="Register">
      <section>Create your account</section>

      <section>
        <label>
          E-mail
          <input
            name="email"
            type="text"
            value={formData.email}
            onChange={onChange}
            placeholder="example@email.com"
          />
        </label>
        <label>
          Nickname
          <input
            name="nickname"
            type="text"
            placeholder="Please write 10 characters or less"
            maxLength={10}
            value={formData.nickname}
            onChange={onChange}
            style={{ flex: 1 }}
          />
        </label>
        <label>
          Password
          <input
            name="password"
            type="password"
            value={formData.password}
            onChange={onChange}
            placeholder="8~20 characters"
          />
        </label>

        <label>
          Password Check
          <input
            name="passwordConfirm"
            type="password"
            value={formData.passwordConfirm}
            onChange={onChange}
          />
        </label>

        <label>
          Gender
          <select name="gender" value={formData.gender} onChange={onChange}>
            {GENDER.map((g) => (
              <option key={g.value} value={g.value}>
                {g.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          Country
          <select name="country" value={formData.country} onChange={onChange}>
            {COUNTRY_OPTIONS.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>
        </label>
      </section>

      <section>
        <button onClick={() => openModal("cancel")}>Cancel</button>
        <button onClick={() => openModal("Register")}>Register</button>
      </section>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onConfirm={handleConfirm}
        message={
          modalType === "cancel"
            ? "Are you sure you want to cancel?"
            : "Do you want to proceed?"
        }
      />
      <hr style={{ margin: "16px 0" }} />

      <h3>Category / Item 선택</h3>
      {error && <div className="errorBox">{error}</div>}

      {stateMeta.loading && !categories.length && <div>카테고리 불러오는 중...</div>}
      {(stateMeta.error || error) && <div className="errorBox">{stateMeta.error || error}</div>}

      {categories.map((c) => (
        <div key={c.category_id ?? c.id} className="card">
          <div style={{ fontWeight: 700, marginBottom: 8 }}>
            {c.category_label_ko ?? c.category_label_en ?? c.label ?? "Category"}
          </div>

          <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
            {(c.items || []).map((it) => {
              const itemId = it.item_id ?? it.id;
              const label = it.item_label_ko ?? it.item_label_en ?? it.label ?? `item#${itemId}`;
              const checked = selectedItemIds.has(itemId);

              return (
                <label key={itemId} style={{ display: "flex", gap: 6, alignItems: "center" }}>
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => toggleItem(itemId)}
                  />
                  {label}
                </label>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}