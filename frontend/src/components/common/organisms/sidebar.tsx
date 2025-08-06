"use client";

import { ForwardIcon, SidebarIcon } from "@/components/common/icons";
import cx from "classnames";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSidebar } from "../../../providers/SidebarProvider";
import HDot from "../icons/HDot";
import OutgoingLogo from "../icons/OutgoingLogo";
import OutgoingLogomark from "../icons/OutgoingLogomark";
import SidebarRuns from "./sidebar-runs";
import ThemeToggle from "../molecules/theme-toggle";

function SidebarItem({
    icon,
    label,
    path,
    className,
    collapsed,
    badge,
    disabled,
}: {
    icon: React.ReactNode;
    label: string;
    path: string;
    className?: string;
    collapsed?: boolean;
    badge?: React.ReactNode;
    disabled?: boolean;
}) {
    const pathname = usePathname();
    const isActive = pathname === path;

    return (
        <div className="relative group">
            <Link
                href={disabled ? "#" : path}
                className={cx(
                    collapsed
                        ? "w-9 h-9 rounded-sm flex items-center justify-center"
                        : "p-2 w-full rounded-sm h-9 flex flex-row items-center text-14-medium-heading text-gray-8 gap-1.5 transition-colors duration-300",
                    isActive ? "bg-gray-3" : "hover:bg-gray-2",
                    className
                )}
            >
                {icon}
                {!collapsed && label}
                {!collapsed && badge && (
                    <div className="text-xs font-medium ml-1.5">{badge}</div>
                )}
            </Link>
            {collapsed && (
                <div className="absolute left-[45px] top-1/2 -translate-y-1/2 px-2 py-1 bg-gray-8 text-gray-1 rounded-sm text-14-medium-heading whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity z-50">
                    {label}
                </div>
            )}
        </div>
    );
}

export default function Sidebar() {
    const { isCollapsed, setIsCollapsed } = useSidebar();

    const sidebarItems = [
        {
            icon: <ForwardIcon />,
            label: "Run",
            path: "/",
        },
    ];

    return (
        <div
            className={cx(
                "hidden md:flex flex-col h-full  transition-all duration-300",
                isCollapsed ? "min-w-[76px] w-[76px] p-5" : "min-w-[296px] p-5 w-[296px]"
            )}
        >
            {!isCollapsed && (
                <div className="w-full flex flex-row justify-between items-between">
                    <div className="flex items-center px-2 h-9">
                        <OutgoingLogo className="text-gray-8" />
                    </div>
                    <button
                        className={cx(
                            "text-gray-6 hover:text-gray-8",
                            isCollapsed && "mx-auto"
                        )}
                        onClick={() => setIsCollapsed(!isCollapsed)}
                        aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                    >
                        <SidebarIcon
                            className={cx(isCollapsed ? "transform rotate-180" : "")}
                        />
                    </button>
                </div>
            )}
            {isCollapsed && (
                <button
                    className={cx("text-gray-6 hover:text-gray-8 mx-auto")}
                    onClick={() => setIsCollapsed(!isCollapsed)}
                    aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                >
                    <SidebarIcon className="mt-2 transform h-5 w-5" />
                </button>
            )}
            {isCollapsed && (
                <div className="mt-5 mb-5 flex justify-center w-5 h-5 mx-auto">
                    <OutgoingLogomark className="text-gray-8" />
                </div>
            )}
            <div
                className={cx(
                    "flex flex-col",
                    isCollapsed ? "items-center space-y-1" : "mt-5 gap-y-1"
                )}
            >
                {sidebarItems.map((item) => (
                    <SidebarItem
                        key={item.label}
                        icon={item.icon}
                        label={item.label}
                        path={item.path}
                        collapsed={isCollapsed}
                        className={cx("text-sm", {
                            "justify-center py-2": isCollapsed,
                        })}
                    />
                ))}
            </div>

            {/* Recent runs section - only show when not collapsed */}
            {!isCollapsed && (
                <div className="mt-5 flex-1 min-h-0">
                    <SidebarRuns />
                </div>
            )}

            {/* Theme toggle at the bottom */}
            <div className={cx("mt-auto", isCollapsed ? "flex justify-center" : "px-2")}>
                <ThemeToggle collapsed={isCollapsed} />
            </div>
        </div>
    );
}
