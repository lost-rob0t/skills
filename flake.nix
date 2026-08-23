{
  description = "Portable reusable agent skills";

  outputs = { self }:
    let
      skills = {
        dotfiles-workflow = ./skills/dotfiles-workflow;
        prolog-reasoning = ./skills/prolog-reasoning;
        rage = ./skills/rage;
        skill-portability = ./skills/skill-portability;
        spec = ./skills/spec;
        zara-mcp = ./skills/zara-mcp;
      };

      targets = {
        opencode = ".config/opencode/skills";
        claude = ".claude/skills";
        agents = ".agents/skills";
        codex = ".codex/skills";
        cursor = ".cursor/skills";
        copilot = ".copilot/skills";
        agent-zero = "usr/skills";
      };

      mkSkillLinksModule = root: { lib, ... }: {
        home.file = lib.mapAttrs' (
          name: source:
          lib.nameValuePair "${root}/${name}" { inherit source; }
        ) skills;
      };

      opencodeModule = { ... }: {
        programs.opencode.skills = skills;
      };

      adapters = {
        opencode = {
          root = targets.opencode;
          inherit skills;
        };
        claude = {
          root = targets.claude;
          inherit skills;
        };
        agents = {
          root = targets.agents;
          inherit skills;
        };
        codex = {
          root = targets.codex;
          inherit skills;
        };
        cursor = {
          root = targets.cursor;
          inherit skills;
        };
        copilot = {
          root = targets.copilot;
          inherit skills;
        };
        agent-zero = {
          root = targets.agent-zero;
          inherit skills;
        };
      };
    in
    {
      lib = {
        inherit skills targets adapters mkSkillLinksModule;
        skillNames = builtins.attrNames skills;

        # Agent Zero's usr/skills path is relative to its installation root,
        # so callers must supply that root instead of receiving a guessed path.
        mkAgentZeroHomeManagerModule = installRoot:
          mkSkillLinksModule "${installRoot}/${targets.agent-zero}";

        # Compatibility for existing dotfiles/consumers while the repository
        # migrates away from the old opencode/ source tree.
        opencodeSkills = skills;
        opencodeSkillNames = builtins.attrNames skills;
      };

      homeManagerModules = {
        default = opencodeModule;
        opencode = opencodeModule;
        claude = mkSkillLinksModule targets.claude;
        agents = mkSkillLinksModule targets.agents;
        codex = mkSkillLinksModule targets.codex;
        cursor = mkSkillLinksModule targets.cursor;
        copilot = mkSkillLinksModule targets.copilot;
      };
    };
}
