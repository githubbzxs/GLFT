import type { ReactNode } from "react";
import { useStyletron } from "baseui";
import { Block } from "baseui/block";
import { HeadingSmall, ParagraphSmall } from "baseui/typography";

type PageHeaderProps = {
  title: string;
  description?: string;
  actions?: ReactNode;
};

export default function PageHeader({ title, description, actions }: PageHeaderProps) {
  const [css] = useStyletron();

  return (
    <Block
      display="flex"
      alignItems="flex-start"
      justifyContent="space-between"
      flexWrap
      marginBottom="scale800"
      className={css({
        gap: "16px"
      })}
    >
      <Block>
        <HeadingSmall marginTop="0" marginBottom="scale200">
          {title}
        </HeadingSmall>
        {description ? (
          <ParagraphSmall marginTop="0" marginBottom="0" color="contentSecondary">
            {description}
          </ParagraphSmall>
        ) : null}
      </Block>
      {actions ? <Block>{actions}</Block> : null}
    </Block>
  );
}
