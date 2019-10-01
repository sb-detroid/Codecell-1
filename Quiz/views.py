from django.shortcuts import render
from django.views.generic import ListView,DetailView,TemplateView
from django.shortcuts import get_object_or_404,render
from django.core.exceptions import PermissionDenied
from django.views import View
from django.http import HttpResponseRedirect,HttpResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from Accounts.models import *
from Quiz.models import *
from Quiz.forms import *

# Create your views here.

class Categories_list_view(ListView):
    model = Category

class View_Quizlist_by_Category(ListView):
    model = Quiz
    template_name = 'Quiz/Quiz_category_list_matching.html'
    context_object_name = 'quiz_list'

    def dispatch(self, request , *args, **kwargs):
        ''' dispatches a url request '''
        self.category = get_object_or_404(Category, category = self.kwargs['category_name'])

        return super(View_Quizlist_by_Category, self).dispatch(request, *args, **kwargs)
        
    def get_context_data(self, **kwargs):
        
        context = super(View_Quizlist_by_Category, self).get_context_data(**kwargs)

        context['category'] = self.category
        
        return context

    def get_queryset(self):
        queryset = super(View_Quizlist_by_Category, self).get_queryset()
        return queryset.filter(category = self.category, draft = False)
    
class Quiz_Detail_View(DetailView):
    model = Quiz
    slug_field = 'url'
    template_name = 'Quiz/quiz_detail.html'

    def get(self, request, *args, **kwargs):
        
        self.object = self.get_object()

        if self.object.draft and not request.user.has_perm('quiz.change_quiz'):
            return PermissionDenied
        
        context = self.get_context_data(object = self.object)
        return render(request,self.template_name,{'quiz':self.object})

class QuizAttempt(View):
    template_name = 'Quiz/attempt.html'
    Quiz_form = QuizForm

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        ''' Process a get request  to attempt quiz '''    

        Quiz_form = self.Quiz_form(kwargs['quiz_name'])

        return render(request,self.template_name,{'Quiz_form':Quiz_form})

    
    def post(self, request, *args, **kwargs):
        ''' Process a post request after user has answered '''
        Quiz_form = self.Quiz_form(kwargs['quiz_name'],request.POST)

        if Quiz_form.is_valid():

            Current_quiz = Quiz.objects.all().filter(title = kwargs['quiz_name'])[0]
            Question_list = MCQ.objects.all().filter(quiz = Current_quiz)

            New_progress = Progress.objects.create(student = request.user, quiz = Current_quiz)
            New_progress.Questions_correct = 0
            New_progress.Questions_attempted = 0
            
            marks = 0
            content = []
            for i in request.POST.keys():

                if i!='csrfmiddlewaretoken':
                    j = []
                    question_name =  Question_list.filter(content = i)[0]
                    j.append(question_name)
                    answer = Answer.objects.all().filter(question = question_name).filter(content = request.POST[i])[0]
                    anslist = [(i,i.correct,True) if i==answer else (i,i.correct,False) for i in Answer.objects.all().filter(question = question_name)]
                    j.append(anslist)
                    New_progress.Questions_attempted += 1
                    if answer.correct:
                        marks += question_name.marks 
                        New_progress.Questions_correct += 1
                    content.append(j)

                
            New_progress.marks = marks
            New_progress.save()   
            return render(request,"Quiz/correct.html",{"content":content,"marks":marks})
            return HttpResponseRedirect(reverse('home'))
        

@login_required
def user_progress(request):
    quiz = []
    progress = Progress.objects.all().filter(student = request.user).order_by('-attempted_on')
    i = 0
    for j in progress:
        context = []
        context.append(j.quiz.title)
        context.append(len(Question.objects.all().filter(quiz = j.quiz)))
        context.append(j.Questions_correct)
        context.append(j.marks)
        #context.append(j.quiz.total_marks())
        if j.marks is 0:
            context.append(0)
        else:
            context.append(str(j.marks/j.quiz.total_marks()*100)[:5])
        context.append(j.attempted_on.date().__str__())
        
        quiz.append(context)
        i += 1
    # context['i'] = i
    
    return render(request,'Quiz/progress.html',{"Quiz": quiz})