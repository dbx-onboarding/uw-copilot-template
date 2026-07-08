// Thin fetch wrapper around the FastAPI backend.
const j = async (url, opts) => {
  const r = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!r.ok) throw new Error(`${r.status} ${url}`);
  return r.json();
};

export const api = {
  me: () => j("/api/me"),
  submissions: () => j("/api/submissions"),
  submission: (id) => j(`/api/submissions/${encodeURIComponent(id)}`),
  claims: (id) => j(`/api/submissions/${encodeURIComponent(id)}/claims`),
  lossRuns: (id) => j(`/api/submissions/${encodeURIComponent(id)}/loss_runs`),
  drivers: (id) => j(`/api/submissions/${encodeURIComponent(id)}/drivers`),
  documents: (id) => j(`/api/submissions/${encodeURIComponent(id)}/documents`),
  similar: (id) => j(`/api/submissions/${encodeURIComponent(id)}/similar`),
  pricing: (id) => j(`/api/submissions/${encodeURIComponent(id)}/pricing`),
  accountIntel: (id) => j(`/api/submissions/${encodeURIComponent(id)}/account-intel`),
  lossDev: (id) => j(`/api/submissions/${encodeURIComponent(id)}/loss-dev`),
  vehicles: (id) => j(`/api/submissions/${encodeURIComponent(id)}/vehicles`),
  policy: (id) => j(`/api/submissions/${encodeURIComponent(id)}/policy`),
  referrals: (id) => j(`/api/submissions/${encodeURIComponent(id)}/referrals`),
  subjectivities: (id) => j(`/api/submissions/${encodeURIComponent(id)}/subjectivities`),
  clearSubjectivity: (id, body) => j(`/api/submissions/${encodeURIComponent(id)}/subjectivities`, { method: "POST", body: JSON.stringify(body) }),
  allClaims: () => j("/api/claims"),
  lossControl: () => j("/api/loss-control"),
  allDocuments: (q = "", category = "") =>
    j(`/api/documents?q=${encodeURIComponent(q)}&category=${encodeURIComponent(category)}`),
  settings: () => j("/api/settings"),
  history: () => j("/api/history"),
  appFeedbackList: () => j("/api/app-feedback"),
  appFeedback: (body) => j("/api/app-feedback", { method: "POST", body: JSON.stringify(body) }),
  chat: (body) => j("/api/chat", { method: "POST", body: JSON.stringify(body) }),
  feedback: (body) => j("/api/feedback", { method: "POST", body: JSON.stringify(body) }),
  decision: (body) => j("/api/decisions", { method: "POST", body: JSON.stringify(body) }),
};
