import type { FormEvent } from "react";
import { useMemo, useState } from "react";
import { Block } from "baseui/block";
import { Button } from "baseui/button";
import { FormControl } from "baseui/form-control";
import { Input } from "baseui/input";
import { KIND } from "baseui/notification";
import { Notification } from "baseui/notification";
import { HeadingLarge, LabelMedium, ParagraphMedium, ParagraphSmall } from "baseui/typography";
import { useStyletron } from "baseui";
import { useLocation, useNavigate } from "react-router-dom";
import api from "../api/client";
import { getErrorMessage } from "../api/errors";
import { setToken, type AuthExpiredReason } from "../api/session";

type LoginResponse = {
  access_token: string;
  token_type: string;
};

type LoginLocationState = {
  reason?: AuthExpiredReason;
  from?: string;
};

const REASON_TEXT: Record<AuthExpiredReason, string> = {
  missing: "请先登录后再访问系统。",
  expired: "登录已过期，请重新登录。",
  unauthorized: "登录状态失效，请重新登录。"
};

export default function LoginPage() {
  const [css, theme] = useStyletron();
  const navigate = useNavigate();
  const location = useLocation();
  const state = (location.state as LoginLocationState | null) ?? null;
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const notice = useMemo(() => {
    if (!state?.reason) {
      return "";
    }
    return REASON_TEXT[state.reason] ?? "";
  }, [state?.reason]);

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const normalizedUsername = username.trim();
    if (!normalizedUsername || !password) {
      setError("请输入账号和密码");
      return;
    }

    setError("");
    setLoading(true);
    try {
      const response = await api.post<LoginResponse>("/auth/login", {
        username: normalizedUsername,
        password
      });
      setToken(response.data.access_token);
      navigate(state?.from || "/", { replace: true });
    } catch (submitError) {
      setError(getErrorMessage(submitError, "登录失败，请检查账号和密码"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Block
      className={css({
        minHeight: "100vh",
        display: "grid",
        gridTemplateColumns: "1.2fr 0.8fr",
        background:
          "radial-gradient(900px 360px at 18% 12%, rgba(69,127,255,0.2), transparent 68%), #070d17",
        "@media screen and (max-width: 980px)": {
          gridTemplateColumns: "1fr"
        }
      })}
    >
      <Block
        paddingTop="scale1200"
        paddingBottom="scale1000"
        paddingLeft="scale1000"
        paddingRight="scale1000"
        display="flex"
        flexDirection="column"
        justifyContent="center"
      >
        <LabelMedium color="contentSecondary" marginTop="0" marginBottom="scale400">
          ALGO MARKET MAKING
        </LabelMedium>
        <HeadingLarge marginTop="0" marginBottom="scale400">
          GLFT 做市系统
        </HeadingLarge>
        <ParagraphMedium color="contentSecondary" marginTop="0" marginBottom="scale900">
          面向 BTC 永续做市的统一控制台，内置策略参数管理、实时风控、告警与引擎控制能力。
        </ParagraphMedium>
        <Block
          className={css({
            display: "grid",
            gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
            gap: theme.sizing.scale500,
            "@media screen and (max-width: 980px)": {
              gridTemplateColumns: "1fr"
            }
          })}
        >
          {[
            { title: "风险优先", value: "实时限额保护" },
            { title: "交易执行", value: "毫秒级刷新" },
            { title: "运维效率", value: "单页集中管理" }
          ].map((item) => (
            <Block
              key={item.title}
              paddingTop="scale500"
              paddingBottom="scale500"
              paddingLeft="scale500"
              paddingRight="scale500"
              className={css({
                border: "1px solid #243452",
                borderRadius: theme.borders.radius500,
                backgroundColor: "rgba(16, 26, 42, 0.72)"
              })}
            >
              <ParagraphSmall color="contentTertiary" marginTop="0" marginBottom="scale200">
                {item.title}
              </ParagraphSmall>
              <LabelMedium color="contentPrimary" marginTop="0" marginBottom="0">
                {item.value}
              </LabelMedium>
            </Block>
          ))}
        </Block>
      </Block>

      <Block
        display="flex"
        justifyContent="center"
        alignItems="center"
        paddingTop="scale1000"
        paddingBottom="scale1000"
        paddingLeft="scale800"
        paddingRight="scale800"
      >
        <Block
          width="100%"
          className={css({
            maxWidth: "440px",
            border: "1px solid #243452",
            borderRadius: theme.borders.radius500,
            backgroundColor: "rgba(12, 20, 32, 0.95)",
            boxShadow: "0 24px 64px rgba(0, 0, 0, 0.42)"
          })}
          paddingTop="scale800"
          paddingBottom="scale800"
          paddingLeft="scale800"
          paddingRight="scale800"
        >
          <LabelMedium color="contentPrimary" marginTop="0" marginBottom="scale600">
            登录系统
          </LabelMedium>
          {notice ? (
            <Notification kind={KIND.info} closeable={false}>
              {notice}
            </Notification>
          ) : null}
          {error ? (
            <Block marginTop="scale500">
              <Notification kind={KIND.negative} closeable={false}>
                {error}
              </Notification>
            </Block>
          ) : null}

          <form onSubmit={onSubmit}>
            <FormControl label="账号">
              <Input
                value={username}
                onChange={(event) => setUsername(event.currentTarget.value)}
                placeholder="请输入账号"
                autoComplete="username"
              />
            </FormControl>
            <FormControl label="密码">
              <Input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.currentTarget.value)}
                placeholder="请输入密码"
                autoComplete="current-password"
              />
            </FormControl>
            <Button
              type="submit"
              isLoading={loading}
              disabled={loading}
              overrides={{
                BaseButton: {
                  style: {
                    width: "100%"
                  }
                }
              }}
            >
              进入控制台
            </Button>
          </form>
        </Block>
      </Block>
    </Block>
  );
}
