{
  description = "Reusable agent skills";

  outputs = { self }:
    let
      opencodeSkills = {
        dotfiles-workflow = ./opencode/dotfiles-workflow;
        prolog-reasoning = ./opencode/prolog-reasoning;
        skill-portability = ./opencode/skill-portability;
      };

      opencodeModule = { ... }: {
        programs.opencode.skills = opencodeSkills;
      };
    in
    {
      lib = {
        inherit opencodeSkills;
        opencodeSkillNames = builtins.attrNames opencodeSkills;
      };

      homeManagerModules = {
        default = opencodeModule;
        opencode = opencodeModule;
      };
    };
}
