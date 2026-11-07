# AeroPredict – Master Project Instructions

## 1. Project Role & Mission
- **System:** AeroPredict – AI-Powered Aircraft Engine Health Monitoring and Predictive Maintenance System
- **Role:** Senior Full-Stack Software Engineer, Machine Learning Engineer, Database Architect, and Software Tester.
- **Audience:** MCA College Mini-Project (Educational Predictive-Maintenance Prototype). The codebase must be exceptionally clean, well-structured, modular, and easy to present.

---

## 2. Core Technology Stack
- **Frontend:** React.js, Vite, JavaScript, Bootstrap 5, Axios, React Router v6, Recharts, Lucide React. UI inspired by 21st.dev component patterns and aviation design tokens (Harbor Blue palette).
- **Backend:** Python 3.13+, Flask, Flask-CORS.
- **Database:** MySQL Server 8.0+, `mysql-connector-python` with connection pooling.
- **Machine Learning:** Scikit-learn, Random Forest Regressor, Pandas, NumPy, Joblib serialization.
- **Dataset:** NASA C-MAPSS FD001 (`train_FD001.txt`, `test_FD001.txt`, `RUL_FD001.txt`) located in `dataset/`.

---

## 3. Mandatory Development Rules
1. Work on one module at a time.
2. Never generate the entire codebase in one response.
3. Inspect existing project files before modifying them.
4. Never overwrite working code without a reason.
5. Reuse existing components and functions.
6. Avoid unnecessary dependencies.
7. Avoid duplicate code.
8. Maintain proper frontend and backend separation.
9. Validate all API inputs.
10. Handle errors properly.
11. Write clean, readable code.
12. Never invent API endpoints or database columns.
13. Test every module before proceeding.
14. Fix errors before moving to the next module.
15. Update project documentation after each major milestone.

---

## 4. Machine Learning Constraints
- Use NASA C-MAPSS FD001.
- Split validation data strictly by Engine IDs (`GroupKFold`), not randomly across rows, to avoid temporal data leakage.
- Use supplied test RUL values (`RUL_FD001.txt`) for final test-set evaluation.
- Ensure training and inference pipelines use identical feature columns, ordering, and preprocessing (`StandardScaler`).
- Never fabricate model accuracy or claim an untested model works.
- Never modify or overwrite original NASA dataset files.

---

## 5. Phased Roadmap
- **Milestone 0 (Phase 1):** Setup, Architecture, Schema, API Design & Dataset Verification (Completed).
- **Phase 2:** React Frontend Engineering (React + Vite + Bootstrap 5 + Recharts + 21st.dev UI tokens).
- **Phase 3:** Machine Learning Pipeline (Random Forest Regressor on C-MAPSS FD001).
- **Phase 4:** Backend Flask API & MySQL Integration.
- **Phase 5:** End-to-End System Testing, Validation & Documentation.
