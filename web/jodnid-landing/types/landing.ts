export interface NavItem {
  label: string;
  href: string;
}

export interface FeatureItem {
  title: string;
  desc: string;
  icon: string;
  color: string;
}

export interface StepItem {
  number: string;
  title: string;
  desc: string;
  icon: React.ReactNode;
}