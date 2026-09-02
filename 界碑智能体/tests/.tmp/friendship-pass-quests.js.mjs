export const FRIENDSHIP_PASS_QUEST = {
  id: "friendship-pass-main",
  title: "寻找友谊关的三个秘密",
  question: "为什么这里会建一座关？",
  evidences: [
    { id: "gate", label: "观察关楼", card: "关隘建筑" },
    { id: "terrain", label: "观察山地与道路", card: "山地通道" },
    { id: "boundary", label: "寻找界碑", card: "边界" },
  ],
};

export const STUDY_POINTS = [
  {
    id: "gate",
    title: "友谊关关楼",
    actionLabel: "观察关楼",
    layoutKey: "gate",
    radius: 3.2,
    type: "study",
    evidence: "gate",
  },
  {
    id: "boundary",
    title: "友谊关界碑",
    actionLabel: "观察界碑",
    layoutKey: "boundary",
    radius: 2.6,
    type: "study",
    evidence: "boundary",
  },
  {
    id: "terrain",
    title: "山地道路观察点",
    actionLabel: "观察地形",
    layoutKey: "terrain",
    radius: 3.0,
    type: "study",
    evidence: "terrain",
  },
];
