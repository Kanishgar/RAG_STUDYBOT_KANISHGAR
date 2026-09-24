// subjects.js - Subject & unit config for Sem 7

export const SUBJECTS = [
  {
    id: "rf",
    name: "RF Passive & Active Circuits",
    shortName: "RF Circuits",
    icon: "📡",
    color: "#EF4444",
    bg: "#FEE2E2",
    units: 5,
  },
  {
    id: "mmc",
    name: "Multimedia Computing",
    shortName: "Multimedia",
    icon: "🎬",
    color: "#F59E0B",
    bg: "#FEF3C7",
    units: 5,
  },
  {
    id: "vr",
    name: "Virtual Reality",
    shortName: "VR",
    icon: "🥽",
    color: "#8B5CF6",
    bg: "#EDE9FE",
    units: 5,
  },
  {
    id: "rdbms",
    name: "Relational Database Management Systems",
    shortName: "RDBMS",
    icon: "🗄️",
    color: "#10B981",
    bg: "#D1FAE5",
    units: 5,
  },
  {
    id: "foc",
    name: "Fiber Optic Communication",
    shortName: "FOC",
    icon: "💡",
    color: "#3B82F6",
    bg: "#DBEAFE",
    units: 5,
  },
];

export const getSubject = (id) => SUBJECTS.find((s) => s.id === id);
