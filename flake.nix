{
  description = "Portable reusable agent skills";

  outputs = { self }:
    let
      skills = {
        adadr = ./skills/adadr;
        activitywatch-analyze = ./skills/activitywatch-analyze;
        activitywatch-group = ./skills/activitywatch-group;
        activitywatch-productivity = ./skills/activitywatch-productivity;
        activitywatch-visualize = ./skills/activitywatch-visualize;
        discover-workflows = ./skills/discover-workflows;
        dotfiles-workflow = ./skills/dotfiles-workflow;
        emacs-eval = ./skills/emacs-eval;
        forgejo-repo-bootstrap = ./skills/forgejo-repo-bootstrap;
        forgejo-skill-edit = ./skills/forgejo-skill-edit;
        git = ./skills/git;
        git-worktrees = ./skills/git-worktrees;
        impeccable = ./skills/impeccable;
        ponytail = ./skills/ponytail;
        ponytail-audit = ./skills/ponytail-audit;
        ponytail-debt = ./skills/ponytail-debt;
        ponytail-gain = ./skills/ponytail-gain;
        ponytail-help = ./skills/ponytail-help;
        ponytail-review = ./skills/ponytail-review;
        prolog-reasoning = ./skills/prolog-reasoning;
        prolog-verification = ./skills/prolog-verification;
        qtile-confirm = ./skills/qtile-confirm;
        qtile-debug = ./skills/qtile-debug;
        qtile-edit = ./skills/qtile-edit;
        qtile-reload = ./skills/qtile-reload;
        rage = ./skills/rage;
        skill-edit = ./skills/skill-edit;
        skill-portability = ./skills/skill-portability;
        spec = ./skills/spec;
        star-lang = ./skills/star-lang;
        starintel-actor-create = ./skills/starintel-actor-create;
        starintel-auto-dig = ./skills/starintel-auto-dig;
        starintel-document-create = ./skills/starintel-document-create;
        starintel-ingest = ./skills/starintel-ingest;
        starintel-local-search = ./skills/starintel-local-search;
        starintel-osint = ./skills/starintel-osint;
        starintel-repo-bootstrap = ./skills/starintel-repo-bootstrap;
        status-update = ./skills/status-update;
        sudo = ./skills/sudo;
        task-steward-bootstrap = ./skills/task-steward-bootstrap;
        task-steward-worker = ./skills/task-steward-worker;
        youtube-context = ./skills/youtube-context;
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
