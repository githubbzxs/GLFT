import { useEffect, useMemo, useState } from "react";
import { Block } from "baseui/block";
import { Button, KIND, SHAPE, SIZE } from "baseui/button";
import { Drawer, ANCHOR } from "baseui/drawer";
import { LabelMedium, ParagraphSmall } from "baseui/typography";
import { useStyletron } from "baseui";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  AUTH_EXPIRED_EVENT,
  clearToken,
  type AuthExpiredReason
} from "../api/session";

type NavItem = {
  to: string;
  label: string;
};

const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "仪表盘" },
  { to: "/orders", label: "订单 / 成交 / 持仓" },
  { to: "/strategy", label: "策略参数" },
  { to: "/risk", label: "风控执行" },
  { to: "/keys", label: "API Key 管理" },
  { to: "/config", label: "系统配置" },
  { to: "/alerts", label: "告警中心" }
];

const useIsMobile = (breakpoint = 980): boolean => {
  const query = `(max-width: ${breakpoint}px)`;
  const [isMobile, setIsMobile] = useState(() => window.matchMedia(query).matches);

  useEffect(() => {
    const mediaQuery = window.matchMedia(query);
    const onChange = (event: MediaQueryListEvent) => setIsMobile(event.matches);
    setIsMobile(mediaQuery.matches);
    mediaQuery.addEventListener("change", onChange);
    return () => mediaQuery.removeEventListener("change", onChange);
  }, [query]);

  return isMobile;
};

export default function Layout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [css, theme] = useStyletron();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const isMobile = useIsMobile();

  useEffect(() => {
    const onAuthExpired = (event: Event) => {
      const reason = (event as CustomEvent<AuthExpiredReason>).detail;
      navigate("/login", {
        replace: true,
        state: { reason, from: location.pathname }
      });
    };

    window.addEventListener(AUTH_EXPIRED_EVENT, onAuthExpired as EventListener);
    return () => {
      window.removeEventListener(AUTH_EXPIRED_EVENT, onAuthExpired as EventListener);
    };
  }, [location.pathname, navigate]);

  const nowText = useMemo(
    () =>
      new Intl.DateTimeFormat("zh-CN", {
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit"
      }).format(new Date()),
    [location.pathname]
  );

  const isActivePath = (to: string) => {
    if (to === "/") {
      return location.pathname === "/";
    }
    return location.pathname.startsWith(to);
  };

  const onLogout = () => {
    clearToken();
    navigate("/login", {
      replace: true,
      state: { reason: "missing", from: location.pathname }
    });
  };

  const onNavigate = (to: string) => {
    navigate(to);
    setDrawerOpen(false);
  };

  const sidebar = (
    <Block
      display="flex"
      flexDirection="column"
      justifyContent="space-between"
      height="100%"
      paddingTop="scale700"
      paddingBottom="scale700"
      paddingLeft="scale700"
      paddingRight="scale700"
      backgroundColor="backgroundSecondary"
    >
      <Block>
        <LabelMedium
          marginTop="0"
          marginBottom="scale700"
          color="contentPrimary"
          className={css({
            letterSpacing: "0.04em"
          })}
        >
          GLFT 做市系统
        </LabelMedium>
        <Block
          display="flex"
          flexDirection="column"
          className={css({
            gap: "10px"
          })}
        >
          {NAV_ITEMS.map((item) => {
            const active = isActivePath(item.to);
            return (
              <Button
                key={item.to}
                kind={KIND.tertiary}
                size={SIZE.compact}
                shape={SHAPE.default}
                onClick={() => onNavigate(item.to)}
                overrides={{
                  BaseButton: {
                    style: {
                      justifyContent: "flex-start",
                      width: "100%",
                      borderRadius: theme.borders.radius400,
                      border: active ? "1px solid #2f4267" : "1px solid transparent",
                      backgroundColor: active
                        ? theme.colors.backgroundTertiary
                        : "transparent",
                      color: active ? theme.colors.contentPrimary : theme.colors.contentSecondary
                    }
                  }
                }}
              >
                {item.label}
              </Button>
            );
          })}
        </Block>
      </Block>

      <Block>
        <ParagraphSmall marginTop="0" marginBottom="scale500" color="contentTertiary">
          当前时间 {nowText}
        </ParagraphSmall>
        <Button
          kind={KIND.secondary}
          size={SIZE.compact}
          onClick={onLogout}
          overrides={{
            BaseButton: {
              style: {
                width: "100%"
              }
            }
          }}
        >
          退出登录
        </Button>
      </Block>
    </Block>
  );

  return (
    <Block
      className={css({
        minHeight: "100vh",
        display: "grid",
        gridTemplateColumns: isMobile ? "1fr" : "280px 1fr",
        background:
          "radial-gradient(1200px 480px at 10% -10%, rgba(67,117,255,0.16), transparent 70%), #070d17"
      })}
    >
      {!isMobile ? (
        <Block
          className={css({
            borderRightWidth: "1px",
            borderRightStyle: "solid",
            borderRightColor: "#243452"
          })}
        >
          {sidebar}
        </Block>
      ) : null}

      <Block display="flex" flexDirection="column" minWidth="0">
        <Block
          display="flex"
          justifyContent="space-between"
          alignItems="center"
          paddingTop="scale500"
          paddingBottom="scale500"
          paddingLeft="scale700"
          paddingRight="scale700"
          className={css({
            borderBottomWidth: "1px",
            borderBottomStyle: "solid",
            borderBottomColor: "#243452",
            backdropFilter: "blur(8px)",
            backgroundColor: "rgba(7, 13, 23, 0.8)"
          })}
        >
          <Block
            display="flex"
            alignItems="center"
            className={css({
              gap: "12px"
            })}
          >
            {isMobile ? (
              <Button
                kind={KIND.tertiary}
                size={SIZE.compact}
                onClick={() => setDrawerOpen(true)}
              >
                菜单
              </Button>
            ) : null}
            <LabelMedium marginTop="0" marginBottom="0">
              GLFT 控制台
            </LabelMedium>
          </Block>
          <ParagraphSmall marginTop="0" marginBottom="0" color="contentSecondary">
            暗色工作台
          </ParagraphSmall>
        </Block>

        <Block flex="1" paddingTop="scale700" paddingBottom="scale700" paddingLeft="scale700" paddingRight="scale700">
          <Outlet />
        </Block>
      </Block>

      {isMobile ? (
        <Drawer
          isOpen={drawerOpen}
          anchor={ANCHOR.left}
          onClose={() => setDrawerOpen(false)}
          size="default"
          autoFocus
          overrides={{
            Root: {
              style: {
                zIndex: 3000
              }
            },
            DrawerBody: {
              style: {
                padding: 0,
                backgroundColor: theme.colors.backgroundSecondary
              }
            }
          }}
        >
          {sidebar}
        </Drawer>
      ) : null}
    </Block>
  );
}
