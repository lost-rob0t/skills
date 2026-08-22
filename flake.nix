{
  description = "Portable reusable agent skills";

  outputs = { self }:
    let
      skills = {
        dotfiles-workflow = ./skills/dotfiles-workflow;
        prolog-reasoning = ./skills/prolog-reasoning;
        skill-portability = ./skills/skill-portability;
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
    in
    {
      lib = {
        inherit skills;
        skillNames = builtins.attrNames skills;

        # Compatibility for existing dotfiles/consumers while the repository
        # migrates away from the old opencode/ source tree.
        opencodeSkills = skills;
        opencodeSkillNames = builtins.attrNames skills;

        targets = {
          opencode = ".config/opencode/skills";
          claude = ".claude/skills";
          agents = ".agents/skills";
          agent-zero = "usr/skills";
        };
      };

      homeManagerModules = {
        default = opencodeModule;
        opencode = opencodeModule;
        claude = mkSkillLinksModule ".claude/skills";
        agents = mkSkillLinksModule ".agents/skills";
      };
    };
}
