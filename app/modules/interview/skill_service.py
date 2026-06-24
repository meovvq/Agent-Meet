"""面试 Skill 加载与管理

从 skills/ 目录加载 SKILL.md + skill.meta.yml，
提供分类分配、参考素材加载等能力。
"""

import logging
from pathlib import Path

import yaml

log = logging.getLogger(__name__)

SKILLS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "skills"


class SkillService:
    """面试方向 Skill 管理（单例缓存）"""

    _skills_cache: dict[str, dict] = {}
    _loaded = False

    @classmethod
    def _ensure_loaded(cls):
        if cls._loaded:
            return
        cls._load_skills()
        cls._loaded = True

    @classmethod
    def _load_skills(cls):
        """启动时加载所有 skill"""
        if not SKILLS_DIR.exists():
            log.warning("Skills 目录不存在: %s", SKILLS_DIR)
            return

        for skill_dir in SKILLS_DIR.iterdir():
            if not skill_dir.is_dir() or skill_dir.name.startswith("_"):
                continue

            skill_md = skill_dir / "SKILL.md"
            meta_yml = skill_dir / "skill.meta.yml"

            if not skill_md.exists() or not meta_yml.exists():
                continue

            try:
                content = skill_md.read_text(encoding="utf-8")
                front_matter, persona = cls._parse_skill_md(content)

                meta = yaml.safe_load(meta_yml.read_text(encoding="utf-8"))

                categories = []
                for cat in meta.get("categories", []):
                    categories.append({
                        "key": cat["key"],
                        "label": cat["label"],
                        "priority": cat.get("priority", "NORMAL"),
                        "ref": cat.get("ref"),
                        "shared": cat.get("shared", False),
                    })

                skill = {
                    "id": skill_dir.name,
                    "name": meta.get("displayName") or front_matter.get("name") or skill_dir.name,
                    "description": front_matter.get("description", ""),
                    "categories": categories,
                    "persona": persona,
                    "display": meta.get("display", {}),
                }
                cls._skills_cache[skill_dir.name] = skill

            except Exception as e:
                log.error("加载 Skill %s 失败: %s", skill_dir.name, e)

    @staticmethod
    def _parse_skill_md(content: str) -> tuple[dict, str]:
        """解析 YAML front matter + Markdown body"""
        front_matter = {}
        body = content

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                front_matter = yaml.safe_load(parts[1]) or {}
                body = parts[2].strip()

        return front_matter, body

    def list_skills(self) -> list[dict]:
        """返回所有 Skill 列表（不含 persona）"""
        self._ensure_loaded()
        return [
            {"id": s["id"], "name": s["name"], "description": s["description"], "display": s.get("display", {})}
            for s in self._skills_cache.values()
        ]

    def get_skill(self, skill_id: str) -> dict:
        """获取 Skill 详情"""
        self._ensure_loaded()
        skill = self._skills_cache.get(skill_id)
        if not skill:
            from app.common.exception import BusinessException, ErrorCode
            raise BusinessException(ErrorCode.NOT_FOUND, f"Skill 不存在: {skill_id}")
        return skill

    def get_persona(self, skill_id: str) -> str:
        """获取面试官人设（SKILL.md body）"""
        self._ensure_loaded()
        skill = self._skills_cache.get(skill_id)
        return skill.get("persona", "") if skill else ""

    def calculate_allocation(self, skill_id: str, question_count: int) -> list[dict]:
        """按优先级分配题目数量（3 阶段）

        Phase 1: ALWAYS_ONE 各 1 题
        Phase 2: 所有分类至少 1 题（CORE 优先）
        Phase 3: 剩余题目按 CORE 优先轮转
        """
        self._ensure_loaded()
        skill = self._skills_cache.get(skill_id)
        if not skill:
            return []

        categories = skill.get("categories", [])
        if not categories:
            return []

        allocation = {}

        # Phase 1: ALWAYS_ONE
        always_one = [c for c in categories if c["priority"] == "ALWAYS_ONE"]
        for cat in always_one:
            allocation[cat["key"]] = 1

        # Phase 2: 至少 1 题
        remaining = question_count - sum(allocation.values())
        core_cats = [c for c in categories if c["priority"] == "CORE" and c["key"] not in allocation]
        normal_cats = [c for c in categories if c["priority"] not in ("CORE", "ALWAYS_ONE") and c["key"] not in allocation]

        for cat in core_cats + normal_cats:
            if remaining <= 0:
                break
            allocation[cat["key"]] = 1
            remaining -= 1

        # Phase 3: 轮转分配
        rotation_order = core_cats + normal_cats
        idx = 0
        while remaining > 0 and rotation_order:
            cat = rotation_order[idx % len(rotation_order)]
            allocation[cat["key"]] = allocation.get(cat["key"], 0) + 1
            remaining -= 1
            idx += 1

        # 构建分配表
        result = []
        cat_map = {c["key"]: c for c in categories}
        for key, count in allocation.items():
            cat = cat_map.get(key, {})
            result.append({
                "key": key,
                "label": cat.get("label", key),
                "count": count,
                "ref": cat.get("ref"),
                "shared": cat.get("shared", False),
            })

        return result

    def load_reference(self, skill_id: str, ref_file: str, shared: bool = False) -> str:
        """加载参考资料（单文件上限 6000 字符）"""
        if shared:
            path = SKILLS_DIR / "_shared" / "references" / ref_file
        else:
            path = SKILLS_DIR / skill_id / "references" / ref_file

        if path.exists():
            content = path.read_text(encoding="utf-8")
            return content[:6000]
        return ""


# 全局单例
skill_service = SkillService()
