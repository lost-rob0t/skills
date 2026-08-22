{
  description = "Reusable agent skills";

  outputs = { self }:
    let
      opencodeSkills = {
        dotfiles-workflow = ./opencode/dotfiles-workflow;
        prolog-reasoning = ./opencode/prolog-reasoning;
        rage = ./opencode/rage;
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
