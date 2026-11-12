(function(){
  'use strict';
  function updateCreator(){
    var role=document.querySelector('.account-form-grid [name="role"]');
    var wrapper=document.querySelector('[data-account-field="instructor"]');
    var input=wrapper&&wrapper.querySelector('select');
    if(!role||!wrapper||!input)return;
    var visible=role.value==='Instructor';
    wrapper.hidden=!visible;
    input.disabled=!visible;
    input.required=visible;
    if(!visible)input.value='';
  }
  function updateRoleRow(form){
    var role=form.querySelector('[name="role"]');
    var profile=form.querySelector('[name="instructor"]');
    if(!role||!profile)return;
    var linked=form.getAttribute('data-linked')==='true';
    var needsProfile=role.value==='Instructor'&&!linked;
    profile.hidden=!needsProfile;
    profile.disabled=!needsProfile;
    profile.required=needsProfile;
    if(!needsProfile)profile.value='';
  }
  document.addEventListener('DOMContentLoaded',function(){
    var creatorRole=document.querySelector('.account-form-grid [name="role"]');
    if(creatorRole){creatorRole.addEventListener('change',updateCreator);updateCreator();}
    document.querySelectorAll('.account-role-form').forEach(function(form){
      var role=form.querySelector('[name="role"]');
      if(role)role.addEventListener('change',function(){updateRoleRow(form);});
      updateRoleRow(form);
    });
  });
})();
