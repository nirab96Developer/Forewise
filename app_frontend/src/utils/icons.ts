// src/utils/icons.ts
// קובץ מרכזי לייבוא איקונים מ-lucide-react ו-react-icons

// ייבוא מ-lucide-react
import * as LucideIcons from "lucide-react";

// ייבוא אייקונים נוספים מ-react-icons
// GiReactor (כחלופה לטרקטור), GiShovel - את חפירה, GiCrane - בנייה, GiHelmet - קסדה
import { 
    GiReactor,  // חלופה לטרקטור
    GiSpade as GiShovel,   // את חפירה (using GiSpade as alternative)
    GiCrane,  // ציוד בנייה
    GiHelmet,  // קסדה (using GiHelmet as alternative)
    GiToolbox   // ארגז כלים
  } from "react-icons/gi";
  
// ייצוא איקונים מ-lucide-react
export const {
  // ניווט ופעולות כלליות
  Home,
  ArrowRight,
  ArrowLeft,
  ChevronDown,
  ChevronUp,
  ChevronLeft,
  ChevronRight,
  X,
  Plus,
  Menu,
  Search,
  Filter,
  LogOut,
  Settings,
  Download,
  Upload,
  Edit,
  Trash,
  
  // סטטוסים והתראות
  CheckCircle,
  XCircle,
  AlertCircle,
  Bell,
  Info,
  
  // זמן ותאריך
  Clock,
  Calendar,
  
  // משתמש ותקשורת
  User,
  Users,
  Eye,
  EyeOff,
  Mail,
  Phone,
  Send,
  
  // פרויקטים וכלים
  Truck,
  Wrench,
  Building2,
  MapPin,
  FileText,
  Folder,
  FolderOpen,
  
  // טעינה והמתנה
  Loader2,
  
  // כללי
  TreeDeciduous,
  History,
  BarChart,
  PieChart,
  CreditCard,
  DollarSign,
  
  // אייקונים נוספים 
  Hammer,
  Axe,
  Cog,
  Cpu,
  Boxes,
  PackageCheck,
  HardDrive
} = LucideIcons;

// ייתכן שהאייקון Tool קיים בגרסה החדשה - בודק קודם
// אם קיים, נשתמש בו; אם לא, נשתמש בחלופה
const ToolIconFromLucide = LucideIcons.Wrench;

// אייקונים עם שמות מותאמים
export const ToolIcon = ToolIconFromLucide;
export const EquipmentIcon = ToolIconFromLucide;
export const ProjectIcon = LucideIcons.Folder;
export const WorkLogIcon = LucideIcons.FileText;
export const AlertIcon = LucideIcons.AlertCircle;
export const SuccessIcon = LucideIcons.CheckCircle;
export const ErrorIcon = LucideIcons.XCircle;
export const InfoIcon = LucideIcons.Info;

// ייצוא האייקונים מ-react-icons
export { GiReactor, GiShovel, GiCrane, GiHelmet, GiToolbox };

// אייקונים חלופיים שמשלבים את שתי הספריות
export const TractorIcon = GiReactor;
export const ConstructionIcon = GiCrane;
export const HardHatIcon = GiHelmet;
export const ShovelIcon = GiShovel;
export const ToolsIcon = GiToolbox;

// ייצוא כל האייקונים כברירת מחדל למקרה של צורך באייקון שלא הוגדר ספציפית
export default LucideIcons;