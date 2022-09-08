from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from bokeh.plotting import figure
from bokeh.embed import components, server_document
from .models import Question, Choice


@login_required
def index(request):
    script, div = bokeh_static_plot()
    latest_question_list = Question.objects.order_by('-pub_date')[:5]
    server_script = server_document("https://demo.bokeh.org/sliders")
    server_document_p = 'https://%s:%s%s' % (
            settings.BOKEH_APPS['BokehApp1']['dest4client'],
            settings.BOKEH_APPS['BokehApp1']['port'],
            settings.BOKEH_APPS['BokehApp1']['url'],
        )
    context = {
        'latest_question_list': latest_question_list,
        'script': script,
        'div': div,
        'server_script': server_script,
        'rt_div': server_document(server_document_p)
    }
    return render(request, 'polls/index.html', context)


@login_required()
def just_app1(request):
    server_document_p = 'http://%s:%s%s' % (
        settings.BOKEH_APPS['BokehApp1']['dest4client'],
        settings.BOKEH_APPS['BokehApp1']['port'],
        settings.BOKEH_APPS['BokehApp1']['url'],
    )
    context = {
        's_script': server_document(server_document_p),
    }
    return render(request, 'polls/just_app1.html', context)


@login_required
def detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, 'polls/detail.html', {'question': question})


@login_required
def results(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, 'polls/results.html', {'question': question})


@login_required
def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(request, 'polls/detail.html', {
            'question': question,
            'error_message': "You didn't select a choice.",
        })
    else:
        selected_choice.votes += 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))


@login_required()
def tmpl(request):
    context = {
    }
    return render(request, 'polls/tmpl.html', context)


def bokeh_static_plot():
    x = [1, 2, 3, 4, 5]
    y = [1, 2, 3, 4, 5]
    plot = figure(
        title='Line Graph',
        x_axis_label='X',
        y_axis_label='Y',
        plot_width=400,
        plot_height=400
    )
    plot.line(x, y, line_width=2)
    script, div = components(plot)
    return script, div
