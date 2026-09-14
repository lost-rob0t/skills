{
  description = "Portable reusable agent skills";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      skills = {
        adadr = ./skills/adadr;
        activitywatch-analyze = ./skills/activitywatch-analyze;
        activitywatch-group = ./skills/activitywatch-group;
        activitywatch-productivity = ./skills/activitywatch-productivity;
        activitywatch-visualize = ./skills/activitywatch-visualize;
        android-adb-deploy = ./skills/android-adb-deploy;
        debug-system = ./skills/debug-system;
        discover-workflows = ./skills/discover-workflows;
        dotfiles-workflow = ./skills/dotfiles-workflow;
        forgejo-repo-bootstrap = ./skills/forgejo-repo-bootstrap;
        forgejo-skill-edit = ./skills/forgejo-skill-edit;
        free-resources = ./skills/free-resources;
        git = ./skills/git;
        git-worktrees = ./skills/git-worktrees;
        impeccable = ./skills/impeccable;
        grill = ./skills/grill;
        merge-on-green = ./skills/merge-on-green;
        opencode-orchestrate = ./skills/opencode-orchestrate;
        opencode-worker = ./skills/opencode-worker;
        ponytail = ./skills/ponytail;
        ponytail-audit = ./skills/ponytail-audit;
        ponytail-debt = ./skills/ponytail-debt;
        ponytail-gain = ./skills/ponytail-gain;
        ponytail-help = ./skills/ponytail-help;
        ponytail-review = ./skills/ponytail-review;
        prolog-project-kb = ./skills/prolog-project-kb;
        prolog-reasoning = ./skills/prolog-reasoning;
        prolog-verification = ./skills/prolog-verification;
        qtile-confirm = ./skills/qtile-confirm;
        qtile-debug = ./skills/qtile-debug;
        qtile-edit = ./skills/qtile-edit;
        qtile-reload = ./skills/qtile-reload;
        rage = ./skills/rage;
        skill-edit = ./skills/skill-edit;
        skill-scope = ./skills/skill-scope;
        skill-portability = ./skills/skill-portability;
        spec = ./skills/spec;
        star-lang = ./skills/star-lang;
        starintel-actor-create = ./skills/starintel-actor-create;
        starintel-auto-dig = ./skills/starintel-auto-dig;
        starintel-credential-lifecycle = ./skills/starintel-credential-lifecycle;
        starintel-document-create = ./skills/starintel-document-create;
        starintel-ingest = ./skills/starintel-ingest;
        starintel-local-search = ./skills/starintel-local-search;
        starintel-osint = ./skills/starintel-osint;
        starintel-repo-bootstrap = ./skills/starintel-repo-bootstrap;
        starintel-spec-version = ./skills/starintel-spec-version;
        starintel-wearos-release = ./skills/starintel-wearos-release;
        status-update = ./skills/status-update;
        sudo = ./skills/sudo;
        task-steward-bootstrap = ./skills/task-steward-bootstrap;
        task-steward-worker = ./skills/task-steward-worker;
        youtube-context = ./skills/youtube-context;
        worker-orchestration = ./skills/worker-orchestration;
        zara-mcp = ./skills/zara-mcp;
      };

      # Agent Zero is GitHub-only. Keep the explicit Forgejo skills in the
      # portable catalog for other consumers, but never expose them through the
      # Agent Zero adapter or Home Manager module.
      agentZeroSkills = builtins.removeAttrs skills [
        "forgejo-repo-bootstrap"
        "forgejo-skill-edit"
      ];

      targets = {
        opencode = ".config/opencode/skills";
        claude = ".claude/skills";
        agents = ".agents/skills";
        codex = ".codex/skills";
        cursor = ".cursor/skills";
        copilot = ".copilot/skills";
        agent-zero = "usr/skills";
      };

      mkSkillLinksModuleFor = skillSet: root: { lib, ... }: {
        home.file = lib.mapAttrs' (
          name: source:
          lib.nameValuePair "${root}/${name}" { inherit source; }
        ) skillSet;
      };

      mkSkillLinksModule = mkSkillLinksModuleFor skills;

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
          skills = agentZeroSkills;
        };
      };
      supportedSystems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = f: builtins.listToAttrs (map (system: {
        name = system;
        value = f system;
      }) supportedSystems);
    in
    {
      lib = {
        inherit skills agentZeroSkills targets adapters mkSkillLinksModule;
        skillNames = builtins.attrNames skills;
        agentZeroSkillNames = builtins.attrNames agentZeroSkills;

        # Agent Zero's usr/skills path is relative to its installation root,
        # so callers must supply that root instead of receiving a guessed path.
        mkAgentZeroHomeManagerModule = installRoot:
          mkSkillLinksModuleFor agentZeroSkills "${installRoot}/${targets.agent-zero}";

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

      packages = forAllSystems (system:
        let pkgs = import nixpkgs { inherit system; };
        in {
          opencode-worker = pkgs.stdenvNoCC.mkDerivation {
            pname = "opencode-worker";
            version = "1.0.0";
            src = ./skills/opencode-worker;
            nativeBuildInputs = [ pkgs.makeWrapper ];
            installPhase = ''
              mkdir -p "$out/lib/opencode-worker" "$out/bin"
              cp -R config scripts "$out/lib/opencode-worker/"
              wrapProgram "$out/lib/opencode-worker/scripts/opencode-worker" \
                --prefix PATH : ${pkgs.lib.makeBinPath [ pkgs.bash pkgs.coreutils pkgs.git pkgs.gnugrep pkgs.python3 pkgs.util-linux ]}
              ln -s "$out/lib/opencode-worker/scripts/opencode-worker" "$out/bin/opencode-worker"
              ln -s "$out/lib/opencode-worker/scripts/resolve-model" "$out/bin/opencode-worker-resolve-model"
            '';
          };
          default = self.packages.${system}.opencode-worker;
        });
    };
}
